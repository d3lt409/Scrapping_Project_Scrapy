import re
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from .constants import tottus
from scrapy.http import Response
from playwright.async_api import Page
import time

class TottusSpider(scrapy.Spider):
    name = "tottus"
    allowed_domains = ["www.tottus.com.pe"]
    
    # Atributos comerciales
    commercial_name = tottus.COMMERCIAL_NAME
    commercial_id = tottus.COMMERCIAL_ID
    
    def __init__(self, custom_urls=None, *args, **kwargs):
        super(TottusSpider, self).__init__(*args, **kwargs)
        
        # Procesar URLs de entrada
        self.start_urls = self._process_input_urls(custom_urls)
    
    def _process_input_urls(self, custom_urls):
        if custom_urls:
            urls = custom_urls.split(',') if isinstance(custom_urls, str) else custom_urls
            cleaned_urls = [url.strip() for url in urls]
            self.logger.info(f"Usando URLs personalizadas: {len(cleaned_urls)} URLs")
            return cleaned_urls
        else:
            # Usar las URLs completas del diccionario CATEGORIAS_MERCADO
            urls = [
                data["url"] 
                for data in tottus.CATEGORIAS_MERCADO.values()
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
                        PageMethod("wait_for_selector", tottus.SELECTOR_PRODUCTS_CONTAINER, timeout=30000),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)")
                    ],
                    playwright_page_goto_kwargs={
                        "wait_until": "domcontentloaded",
                        "timeout": 20000
                    },
                    category_index=i,  
                    original_url=url,
                    max_retry_times=3
                ),
                callback=self.parse_category,
                dont_filter=True,
                headers={'X-Category-Index': str(i)},
                errback=self.handle_error
            )

    def handle_error(self, failure):
        """Manejar errores de requests incluyendo timeouts"""
        request = failure.request
        category_index = request.meta.get("category_index", "unknown")
        original_url = request.meta.get("original_url", request.url)
        
        # Obtener información de la URL
        url_parts = original_url.split('/')
        if len(url_parts) >= 2:
            categoria = url_parts[-2].replace('-', ' ').title()
            subcategoria = url_parts[-1].replace('-', ' ').title()
        else:
            categoria = "Unknown"
            subcategoria = "Unknown"
        
        if "TimeoutError" in str(failure.type):
            self.logger.warning(f"Timeout en Request #{category_index}: {categoria} > {subcategoria}")
            self.logger.warning(f"URL afectada: {original_url}")
            
            # Intentar un reintento con timeout más largo
            retry_count = request.meta.get('retry_count', 0)
            if retry_count < 2:
                self.logger.info(f"Reintentando Request #{category_index} (intento {retry_count + 1})")
                retry_request = request.replace(
                    meta={
                        **request.meta,
                        'retry_count': retry_count + 1,
                        'playwright_page_goto_kwargs': {
                            "wait_until": "domcontentloaded",
                            "timeout": 45000
                        }
                    }
                )
                return retry_request
            else:
                self.logger.error(f"Máximo de reintentos alcanzado para Request #{category_index}: {categoria} > {subcategoria}")
        else:
            self.logger.error(f"Error en Request #{category_index}: {categoria} > {subcategoria} - {failure}")

    async def parse_category(self, response: Response):
        """Parsear una categoría completa con paginación"""
        page: Page = response.meta["playwright_page"]
        category_index = response.meta.get("category_index", "unknown")
        original_url = response.meta.get("original_url", response.url)
        
        # Extraer nombre de categoría usando la función utilitaria
        categoria_name = tottus.get_category_name_from_url(original_url)
        main_category = tottus.get_main_category_from_tottus_category(categoria_name)
        
        self.logger.info(f"INICIANDO Request #{category_index} para: {main_category} > {categoria_name}")

        if page.url != original_url:
            self.logger.info(f"Navegando explícitamente a URL original: {original_url}")
            try:
                await page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                self.logger.error(f"Error navegando a {original_url}: {e}")
                return
        
        self.logger.info(f"Procesando categoría: {main_category} > {categoria_name}")
        
        page_number = 1
        max_pages = 200
        total_products_scraped = 0
        consecutive_empty_pages = 0
        max_consecutive_empty = 3
        
        while page_number <= max_pages:
            self.logger.info(f"Scrapeando página {page_number} de '{main_category} > {categoria_name}'...")

            await self.await_products_loaded(page)

            html_content = await page.content()
            scrapy_selector = scrapy.Selector(text=html_content)
            products_found = 0
            products_elements = scrapy_selector.xpath(tottus.XPATH_PRODUCTS)
            
            self.logger.info(f"Elementos de producto encontrados: {len(products_elements)}")
            
            for product_element in products_elements:
                item = self.extract_product_data(product_element, main_category, categoria_name)
                if item:
                    products_found += 1
                    total_products_scraped += 1
                    yield item
                else:
                    self.logger.debug("Producto sin datos válidos, omitido")

            self.logger.info(f"Productos válidos extraídos en página {page_number}: {products_found}")
            self.logger.info(f"Total acumulado para '{main_category} > {categoria_name}': {total_products_scraped}")

            # Manejar páginas vacías
            if products_found == 0:
                consecutive_empty_pages += 1
                self.logger.warning(f"Página {page_number} sin productos válidos. Páginas vacías consecutivas: {consecutive_empty_pages}/{max_consecutive_empty}")
                
                if consecutive_empty_pages >= max_consecutive_empty:
                    self.logger.info(f"Demasiadas páginas vacías consecutivas ({consecutive_empty_pages}). Terminando categoría '{main_category} > {categoria_name}'")
                    break
                    
                if len(products_elements) == 0 and consecutive_empty_pages == 1:
                    self.logger.info("Reintentando página actual una vez más...")
                    await page.wait_for_timeout(2000)
                    consecutive_empty_pages = 0
                    continue
            else:
                consecutive_empty_pages = 0
            
            # Verificar si hay siguiente página
            has_next_page = await self.go_to_next_page(page, scrapy_selector)
            
            if not has_next_page:
                self.logger.info(f"No hay más páginas para '{main_category} > {categoria_name}' después de página {page_number}")
                break
                
            page_number += 1
            await page.wait_for_timeout(500)
        
        # Resumen final
        if page_number > max_pages:
            self.logger.warning(f"Alcanzado límite máximo de páginas ({max_pages}) para '{main_category} > {categoria_name}'")
        elif consecutive_empty_pages >= max_consecutive_empty:
            self.logger.info(f"Categoría terminada por páginas vacías consecutivas ({consecutive_empty_pages}) en '{main_category} > {categoria_name}'")
        
        self.logger.info(f"RESUMEN '{main_category} > {categoria_name}': {total_products_scraped} productos en {page_number} páginas")
        self.logger.info(f"Request #{category_index} COMPLETADO: '{main_category} > {categoria_name}' - Lista para siguiente")
        
        # Cerrar página
        try:
            if not page.is_closed():
                await page.close()
                self.logger.debug(f"Página cerrada correctamente para '{main_category} > {categoria_name}'")
        except Exception as e:
            self.logger.warning(f"Error cerrando página: {e}")

    def extract_product_data(self, product_element, main_category, subcategoria):
        try:
            # Información básica del producto
            name_list = product_element.xpath(tottus.XPATH_PRODUCT_NAME).getall()
            if not name_list:
                return None
            name = name_list[0].strip()
            
            # Precio actual
            price_list = product_element.xpath(tottus.XPATH_PRODUCT_CURRENT_PRICE).getall()
            if not price_list:
                # Intentar extraer precio del texto si no hay data-internet-price
                price_text_list = product_element.xpath(tottus.XPATH_PRODUCT_PRICE).getall()
                if price_text_list:
                    price_raw = price_text_list[0]
                    price = float(re.sub(r'[^\d.]', '', price_raw))
                else:
                    return None
            else:
                price = float(price_list[0])
            
            # Calcular datos de unidad
            unit_price, total_unit_quantity, unit_type = self.calculate_unit_data(
                price, name, ""
            )
            
            # Determinar categoría principal usando la función de clasificación
            main_category = tottus.get_main_category_from_tottus_category(subcategoria)
            
            # Crear item con solo los campos básicos
            item = ScraperItem()
            
            # Campos básicos requeridos por la base de datos
            item['name'] = name
            item['price'] = price
            item['unit_price'] = unit_price
            item['total_unit_quantity'] = total_unit_quantity
            item['unit_type'] = unit_type
            item['category'] = main_category  # Usar la categoría principal determinada automáticamente
            item['sub_category'] = subcategoria  # Mantener la subcategoría original de Tottus
            item['comercial_name'] = tottus.COMMERCIAL_NAME
            item['comercial_id'] = tottus.COMMERCIAL_ID
            
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
                
                # Normalizar unidades
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
            
            # Intentar múltiples selectores
            selectors_to_try = [
                tottus.SELECTOR_PRODUCTS_CONTAINER,
                "div[class*='product']",
                ".product",
                "[data-testid*='product']"
            ]
            
            success = False
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=30000)
                    self.logger.info(f"Productos encontrados con selector: {selector}")
                    success = True
                    break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} falló: {e}")
                    continue
            
            if not success:
                self.logger.warning("Ningún selector de productos funcionó, continuando sin esperar")
                
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            self.logger.warning(f"Timeout o error esperando productos: {e}")

    async def go_to_next_page(self, page: Page, scrapy_selector):
        try:
            if page.is_closed():
                self.logger.error("Página cerrada, no se puede navegar")
                return False

            # Verificar que existe el contenedor de paginación
            pagination_element = scrapy_selector.xpath(tottus.XPATH_PAGINATION).get()
            if not pagination_element:
                self.logger.info("No se encontró elemento de paginación")
                return False

            # Obtener página activa actual
            active_page_list = scrapy_selector.xpath(tottus.XPATH_ACTIVE_PAGE).getall()
            if not active_page_list:
                self.logger.info("No se encontró página activa")
                return False
            
            current_page = int(active_page_list[0])
            self.logger.info(f"Página actual: {current_page}")
            
            # Obtener todas las páginas disponibles (incluyendo el último número visible)
            all_pages = scrapy_selector.xpath(tottus.XPATH_ALL_PAGES).getall()
            all_page_numbers = []
            max_visible_page = current_page
            
            for p in all_pages:
                if p.isdigit():
                    page_num = int(p)
                    all_page_numbers.append(page_num)
                    max_visible_page = max(max_visible_page, page_num)
            
            # También buscar si hay un número máximo en botones deshabilitados o textos "..."
            # En tu HTML hay un botón con "37" que indica la página máxima
            max_page_elements = scrapy_selector.xpath('//button[contains(@id, "testId-pagination-bottom-button") and @disabled]//p//text()').getall()
            for max_elem in max_page_elements:
                if max_elem.isdigit():
                    max_visible_page = max(max_visible_page, int(max_elem))
            
            self.logger.info(f"Páginas detectadas: {sorted(all_page_numbers)}, Máxima visible: {max_visible_page}")
            
            # Verificar si podemos navegar a la siguiente página
            next_page_number = current_page + 1
            
            # Primero intentar con el botón específico de la página
            specific_page_xpath = tottus.XPATH_SPECIFIC_PAGE_BUTTON.format(next_page_number)
            next_page_element = await page.query_selector(f'xpath={specific_page_xpath}')
            
            # Si no hay botón específico, usar el botón de flecha derecha
            if not next_page_element:
                next_page_element = await page.query_selector(f'xpath={tottus.XPATH_NEXT_PAGE_BUTTON}')
                # Verificar que no esté deshabilitado
                if next_page_element:
                    is_disabled = await next_page_element.get_attribute('disabled')
                    if is_disabled is not None:
                        self.logger.info(f"Botón de siguiente página está deshabilitado. Hemos llegado al final.")
                        return False
            
            if next_page_element:
                await next_page_element.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                
                self.logger.info(f"Haciendo clic para navegar a página {next_page_number}")
                await next_page_element.click()
                
                # Esperar a que la página cargue
                await page.wait_for_timeout(1500)
                await self.await_products_loaded(page)
                
                # Verificar que realmente cambió la página
                new_html = await page.content()
                new_selector = scrapy.Selector(text=new_html)
                new_active_page = new_selector.xpath(tottus.XPATH_ACTIVE_PAGE).getall()
                
                if new_active_page and int(new_active_page[0]) == next_page_number:
                    self.logger.info(f"✅ Navegación exitosa a página {new_active_page[0]}")
                    return True
                else:
                    self.logger.warning(f"❌ No se detectó cambio correcto de página. Esperado: {next_page_number}, Obtenido: {new_active_page}")
                    return False
                
            else:
                self.logger.info("No se encontró botón para la siguiente página - fin de paginación")
                return False
                
        except Exception as e:
            self.logger.error(f"Error navegando a siguiente página: {e}")
            import traceback
            traceback.print_exc()
            return False
