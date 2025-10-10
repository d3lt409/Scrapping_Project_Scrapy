import re
import scrapy
from scrapy_playwright.page import PageMethod
from shared_items import SharedSupermercadoItem
from .constants import plaza_vea
from scrapy.http import Response
from playwright.async_api import Page
import time


class PlazaVeaSpider(scrapy.Spider):
    name = "plaza_vea"
    allowed_domains = ["www.plazavea.com.pe"]
    
    def __init__(self, custom_urls=None, *args, **kwargs):
        super(PlazaVeaSpider, self).__init__(*args, **kwargs)
        
        # Procesar URLs de entrada
        self.start_urls = self._process_input_urls(custom_urls)
    
    def _process_input_urls(self, custom_urls):
        if custom_urls:
            urls = custom_urls.split(',') if isinstance(custom_urls, str) else custom_urls
            cleaned_urls = [url.strip() for url in urls]
            self.logger.info(f"Usando URLs personalizadas: {len(cleaned_urls)} URLs")
            return cleaned_urls
        else:
            urls = [
                plaza_vea.BASE_URL + plaza_vea.CATEGORIA_URL_TEMPLATE.format(
                    categoria=categoria, subcategoria=subcategoria
                )
                for categoria, subcategorias in plaza_vea.CATEGORIAS_MERCADO.items()
                for subcategoria in subcategorias
            ]
            self.logger.info(f"URLs generadas automáticamente: {len(urls)} URLs")
            return urls

    def start_requests(self):
        for i, url in enumerate(self.start_urls):
            unique_url = f"{url}?scrapy_index={i}&ts={int(time.time())}"
            yield scrapy.Request(
                unique_url,
                meta=dict(
                    playwright=True, 
                    playwright_include_page=True,  
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", plaza_vea.SELECTOR_PRODUCTS_CONTAINER, timeout=8000),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)")
                    ],
                    playwright_page_goto_kwargs={
                        "wait_until": "domcontentloaded",
                        "timeout": 15000
                    },
                    category_index=i,  
                    original_url=url   
                ),
                callback=self.parse_category,
                dont_filter=True,  
                headers={'X-Category-Index': str(i)} 
            )

    async def parse_category(self, response: Response):
        """Parsear una categoría completa con paginación"""
        page: Page = response.meta["playwright_page"]
        category_index = response.meta.get("category_index", "unknown")
        original_url = response.meta.get("original_url", response.url)
        
        url_parts = original_url.split('/')
        categoria = url_parts[-2].replace('-', ' ').title()
        subcategoria = url_parts[-1].replace('-', ' ').title()
        
        self.logger.info(f"INICIANDO Request #{category_index} para: {categoria} > {subcategoria}")

        if page.url != original_url:
            self.logger.info(f"Navegando explícitamente a URL original: {original_url}")
            try:
                await page.goto(original_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1000)  
            except Exception as e:
                self.logger.error(f"Error navegando a {original_url}: {e}")
                return
        
        self.logger.info(f"Procesando categoría: {categoria} > {subcategoria}")
        
        page_number = 1
        max_pages = 200
        total_products_scraped = 0
        consecutive_empty_pages = 0
        max_consecutive_empty = 3  # Máximo 3 páginas vacías consecutivas antes de pasar a siguiente categoría
        
        while page_number <= max_pages:
            self.logger.info(f"Scrapeando página {page_number} de '{categoria} > {subcategoria}'...")

            await self.await_products_loaded(page)

            html_content = await page.content()
            scrapy_selector = scrapy.Selector(text=html_content)
            products_found = 0
            products_elements = scrapy_selector.xpath(plaza_vea.XPATH_PRODUCTS)
            
            self.logger.info(f"Elementos de producto encontrados: {len(products_elements)}")
            
            for product_element in products_elements:
                item = self.extract_product_data(product_element, categoria, subcategoria)
                if item:
                    products_found += 1
                    total_products_scraped += 1
                    yield item
                else:
                    self.logger.debug("Producto sin datos válidos, omitido")

            self.logger.info(f"Productos válidos extraídos en página {page_number}: {products_found}")
            self.logger.info(f"Total acumulado para '{categoria} > {subcategoria}': {total_products_scraped}")

            # Manejar páginas vacías o sin productos válidos
            if products_found == 0:
                consecutive_empty_pages += 1
                self.logger.warning(f"⚠️ Página {page_number} sin productos válidos. Páginas vacías consecutivas: {consecutive_empty_pages}/{max_consecutive_empty}")
                
                # Si hay demasiadas páginas vacías consecutivas, terminar esta categoría
                if consecutive_empty_pages >= max_consecutive_empty:
                    self.logger.info(f"🛑 Demasiadas páginas vacías consecutivas ({consecutive_empty_pages}). Terminando categoría '{categoria} > {subcategoria}'")
                    break
                    
                # Si no hay elementos de producto, esperar y reintentar la misma página una vez
                if len(products_elements) == 0 and consecutive_empty_pages == 1:
                    self.logger.info("Reintentando página actual una vez más...")
                    await page.wait_for_timeout(2000)
                    consecutive_empty_pages = 0  # Reset para dar una segunda oportunidad
                    continue
            else:
                # Reset contador si encontramos productos
                consecutive_empty_pages = 0
            
            # Verificar si hay siguiente página
            has_next_page = await self.go_to_next_page(page, scrapy_selector)
            
            if not has_next_page:
                self.logger.info(f"No hay más páginas para '{categoria} > {subcategoria}' después de página {page_number}")
                break
                
            page_number += 1
            await page.wait_for_timeout(500)  
        
        # Resumen final de la categoría
        if page_number > max_pages:
            self.logger.warning(f"Alcanzado límite máximo de páginas ({max_pages}) para '{categoria} > {subcategoria}'")
        elif consecutive_empty_pages >= max_consecutive_empty:
            self.logger.info(f"Categoría terminada por páginas vacías consecutivas ({consecutive_empty_pages}) en '{categoria} > {subcategoria}'")

        self.logger.info(f"RESUMEN '{categoria} > {subcategoria}': {total_products_scraped} productos en {page_number} páginas")
        self.logger.info(f"Request #{category_index} COMPLETADO: '{categoria} > {subcategoria}' - Lista para siguiente")

        # Cerrar página para liberar recursos antes de pasar a siguiente categoría
        try:
            if not page.is_closed():
                await page.close()
                self.logger.debug(f"Página cerrada correctamente para '{categoria} > {subcategoria}'")
        except Exception as e:
            self.logger.warning(f"Error cerrando página: {e}")

    def extract_product_data(self, product_element, categoria, subcategoria):
        try:
            name_list = product_element.xpath(plaza_vea.XPATH_PRODUCT_NAME).getall()
            if not name_list:
                return None
            name = name_list[0].strip()
            
            price_list = product_element.xpath(plaza_vea.XPATH_PRODUCT_PRICE).getall()
            if not price_list:
                return None
            
            price_raw = price_list[0]
            price = float(re.sub(r'[^\d.]', '', price_raw))
            
            unit_reference_list = product_element.xpath(plaza_vea.XPATH_PRODUCT_UNIT_REFERENCE).getall()
            unit_reference = unit_reference_list[0].strip() if unit_reference_list else ""
            
            unit_price, total_unit_quantity, unit_type = self.calculate_unit_data(
                price, name, unit_reference
            )
            
            item = SharedSupermercadoItem()
            item['name'] = name
            item['price'] = price
            item['unit_price'] = unit_price
            item['total_unit_quantity'] = total_unit_quantity
            item['unit_type'] = unit_type
            item['category'] = categoria
            item['sub_category'] = subcategoria
            
            item['comercial_name'] = 'PlazaVea'
            item['comercial_id'] = 'plazavea_peru'
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error extrayendo producto: {e}")
            return None

    def calculate_unit_data(self, price, name, unit_reference):
        try:
            text_to_analyze = f"{name} {unit_reference}".lower()
            
            pattern = r'(\d+(?:\.\d+)?)\s*(kg|g|gr|grs|l|litro|litros|ml|mililitro|mililitros|pack|paquete|caja|bandeja|unidad|unidades|un|u|und|unds)\b'
            matches = re.findall(pattern, text_to_analyze, re.IGNORECASE)
            
            if matches:
                quantity_str, unit_str = matches[-1]
                quantity = float(quantity_str.replace(',', '.'))
                
                # Normalizar variantes de unidades
                unit_normalized = {
                    'g': 'g', 'gr': 'g', 'grs': 'g',
                    'l': 'l', 'litro': 'l', 'litros': 'l', 
                    'ml': 'ml', 'mililitro': 'ml', 'mililitros': 'ml',
                    'pack': 'pack', 'paquete': 'pack', 'caja': 'pack',
                    'bandeja': 'g',
                    'unidades': 'unidad', 'un': 'unidad', 'u': 'unidad', 'und': 'unidad', 'unds': 'unidad'
                }.get(unit_str.lower(), unit_str.lower())

                # Calcular según tipo de unidad
                if unit_normalized in ['g', 'kg', 'l', 'ml']:
                    if unit_str.lower() == 'bandeja':
                        return price, quantity, 'g'
                    else:
                        return price / quantity, quantity, unit_normalized
                elif unit_normalized == 'pack':
                    return price / quantity, quantity, 'pack'
                elif unit_normalized == 'unidad':
                    return price / quantity if quantity > 1 else price, quantity if quantity > 1 else 1.0, 'unidad'
                else:
                    return price / quantity, quantity, unit_normalized
            
            # Si no hay coincidencias, asumir 1 unidad
            return price, 1.0, 'unidad'
                
        except Exception as e:
            self.logger.error(f"Error calculando datos de unidad: {e}")
            return price, 1.0, 'unidad'

    async def await_products_loaded(self, page: Page):
        try:
            if page.is_closed():
                self.logger.error("Página cerrada prematuramente")
                return
            
            await page.wait_for_selector(plaza_vea.SELECTOR_PRODUCTS_CONTAINER, timeout=4000)
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)    
            
        except Exception as e:
            self.logger.warning(f"Timeout o error esperando productos: {e}")


    async def go_to_next_page(self, page: Page, scrapy_selector):
        try:
            if page.is_closed():
                self.logger.error("Página cerrada, no se puede navegar")
                return False

            pagination_element = scrapy_selector.xpath(plaza_vea.XPATH_PAGINATION).get()
            if not pagination_element:
                self.logger.info("No se encontró elemento de paginación")
                return False

            active_page_list = scrapy_selector.xpath(plaza_vea.XPATH_ACTIVE_PAGE).getall()
            if not active_page_list:
                self.logger.info("No se encontró página activa")
                return False
            
            current_page = int(active_page_list[0])
            self.logger.info(f"Página actual: {current_page}")
            
            all_pages = scrapy_selector.xpath(plaza_vea.XPATH_ALL_PAGES).getall()
            all_page_numbers = [int(p) for p in all_pages if p.isdigit()]
            max_page = max(all_page_numbers) if all_page_numbers else current_page
            
            self.logger.info(f"Páginas disponibles: {sorted(all_page_numbers)}, Máxima: {max_page}")
            
            if current_page >= max_page:
                self.logger.info(f"Ya estamos en la última página ({current_page}/{max_page})")
                return False
            
            next_page_number = current_page + 1
            
            # Usar XPath optimizado desde constantes
            specific_page_xpath = plaza_vea.XPATH_SPECIFIC_PAGE_BUTTON.format(next_page_number)
            next_page_element = await page.query_selector(f'xpath={specific_page_xpath}')
            
            if not next_page_element:
                # Fallback: primer botón de página disponible
                next_page_element = await page.query_selector(f'xpath={plaza_vea.XPATH_NEXT_PAGE_BUTTON}')
            
            if next_page_element:
                await next_page_element.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)  
                
                self.logger.info(f"Haciendo clic para navegar a página {next_page_number}")
                await next_page_element.click()
                
                await page.wait_for_timeout(1500) 
                await self.await_products_loaded(page)
                
                new_html = await page.content()
                new_selector = scrapy.Selector(text=new_html)
                new_active_page = new_selector.xpath(plaza_vea.XPATH_ACTIVE_PAGE).getall()
                
                if new_active_page and int(new_active_page[0]) == next_page_number:
                    self.logger.info(f"Navegación exitosa a página {new_active_page[0]}")
                    return True
                else:
                    self.logger.warning(f"No se detectó cambio correcto de página. Esperado: {next_page_number}, Obtenido: {new_active_page}")
                    return False
                
            else:
                self.logger.info("No se encontró botón para la siguiente página")
                return False
                
        except Exception as e:
            self.logger.error(f"Error navegando a siguiente página: {e}")
            import traceback
            traceback.print_exc()
            return False
