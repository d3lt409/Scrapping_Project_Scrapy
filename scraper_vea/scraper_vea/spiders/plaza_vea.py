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
        self.start_urls = []
        
        # Si se proporcionan URLs personalizadas, usarlas
        if custom_urls:
            if isinstance(custom_urls, str):
                # Si es una cadena, dividir por comas
                self.start_urls = [url.strip() for url in custom_urls.split(',')]
            elif isinstance(custom_urls, list):
                self.start_urls = custom_urls
            self.logger.info(f"🎯 Usando URLs personalizadas: {len(self.start_urls)} URLs")
        else:
            # Generar URLs para todas las categorías y subcategorías
            for categoria, subcategorias in plaza_vea.CATEGORIAS_MERCADO.items():
                for subcategoria in subcategorias:
                    url = plaza_vea.BASE_URL + plaza_vea.CATEGORIA_URL_TEMPLATE.format(
                        categoria=categoria, 
                        subcategoria=subcategoria
                    )
                    self.start_urls.append(url)
            self.logger.info(f"📦 URLs generadas automáticamente: {len(self.start_urls)} URLs")
        
        # Mostrar resumen de URLs
        for i, url in enumerate(self.start_urls[:5], 1):  # Mostrar solo las primeras 5
            self.logger.info(f"   {i}. {url}")
        if len(self.start_urls) > 5:
            self.logger.info(f"   ... y {len(self.start_urls) - 5} URLs más")

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(
                    playwright=True, 
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", plaza_vea.SELECTOR_PRODUCTS_CONTAINER, timeout=30000),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)")
                    ],
                    playwright_page_goto_kwargs={
                        "wait_until": "domcontentloaded",
                        "timeout": 60000
                    }
                ),
                callback=self.parse_category
            )

    async def parse_category(self, response: Response):
        """Parsear una categoría completa con paginación"""
        page: Page = response.meta["playwright_page"]
        
        # Extraer categoria y subcategoria de la URL
        url_parts = response.url.split('/')
        categoria = url_parts[-2].replace('-', ' ').title()
        subcategoria = url_parts[-1].replace('-', ' ').title()
        
        page_number = 1
        max_pages = 50  # Límite de seguridad para evitar loops infinitos
        total_products_scraped = 0
        
        while page_number <= max_pages:
            self.logger.info(f"🔍 Scrapeando página {page_number} de '{categoria} > {subcategoria}'...")
            
            # Esperar a que los productos se carguen
            await self.await_products_loaded(page)
            
            # Obtener contenido HTML y crear selector
            html_content = await page.content()
            scrapy_selector = scrapy.Selector(text=html_content)
            
            # Extraer productos de la página actual
            products_found = 0
            products_elements = scrapy_selector.xpath(plaza_vea.XPATH_PRODUCTS)
            
            self.logger.info(f"📦 Elementos de producto encontrados: {len(products_elements)}")
            
            for product_element in products_elements:
                item = self.extract_product_data(product_element, categoria, subcategoria)
                if item:
                    products_found += 1
                    total_products_scraped += 1
                    yield item
                else:
                    self.logger.debug("⚠️ Producto sin datos válidos, omitido")
            
            self.logger.info(f"✅ Productos válidos extraídos en página {page_number}: {products_found}")
            self.logger.info(f"📊 Total acumulado para '{categoria} > {subcategoria}': {total_products_scraped}")
            
            # Si no se encontraron productos válidos, puede ser que la página no haya cargado bien
            if products_found == 0 and len(products_elements) == 0:
                self.logger.warning(f"⚠️ Página {page_number} sin productos. Reintentando...")
                await page.wait_for_timeout(5000)
                continue
            
            # Verificar si hay siguiente página
            has_next_page = await self.go_to_next_page(page, scrapy_selector)
            
            if not has_next_page:
                self.logger.info(f"📄 No hay más páginas para '{categoria} > {subcategoria}' después de página {page_number}")
                break
                
            page_number += 1
            
            # Pausa entre páginas para no saturar el servidor
            await page.wait_for_timeout(2000)
        
        if page_number > max_pages:
            self.logger.warning(f"⚠️ Alcanzado límite máximo de páginas ({max_pages}) para '{categoria} > {subcategoria}'")
        
        self.logger.info(f"🎯 RESUMEN '{categoria} > {subcategoria}': {total_products_scraped} productos en {page_number} páginas")

    def extract_product_data(self, product_element, categoria, subcategoria):
        """Extraer datos de un producto individual"""
        try:
            # Extraer nombre del producto
            name_list = product_element.xpath(plaza_vea.XPATH_PRODUCT_NAME).getall()
            if not name_list:
                return None
            name = name_list[0].strip()
            
            # Extraer precio
            price_list = product_element.xpath(plaza_vea.XPATH_PRODUCT_PRICE).getall()
            if not price_list:
                return None
            
            # Limpiar precio (solo números y punto decimal)
            price_raw = price_list[0]
            price = float(re.sub(r'[^\d.]', '', price_raw))
            
            # Extraer referencia de unidades
            unit_reference_list = product_element.xpath(plaza_vea.XPATH_PRODUCT_UNIT_REFERENCE).getall()
            unit_reference = unit_reference_list[0].strip() if unit_reference_list else ""
            
            # Determinar unit_price y total_unit_quantity
            unit_price, total_unit_quantity, unit_type = self.calculate_unit_data(
                price, name, unit_reference
            )
            
            # Crear item
            item = SharedSupermercadoItem()
            item['name'] = name
            item['price'] = price
            item['unit_price'] = unit_price
            item['total_unit_quantity'] = total_unit_quantity
            item['unit_type'] = unit_type
            item['category'] = categoria
            item['sub_category'] = subcategoria
            # comercial_name y comercial_id se establecen automáticamente en el item
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error extrayendo producto: {e}")
            return None

    def calculate_unit_data(self, price, name, unit_reference):
        """Calcular unit_price, total_unit_quantity y unit_type"""
        try:
            # Buscar unidades en el nombre o referencia
            text_to_analyze = f"{name} {unit_reference}".lower()
            
            # Patrones para detectar unidades
            kg_pattern = r'(\d+(?:\.\d+)?)\s*kg'
            g_pattern = r'(\d+(?:\.\d+)?)\s*g(?!\s*kg)'  # gramos pero no kilogramos
            l_pattern = r'(\d+(?:\.\d+)?)\s*l'
            ml_pattern = r'(\d+(?:\.\d+)?)\s*ml'
            unidad_pattern = r'(\d+)\s*(?:unidad|un|u\b)'
            pack_pattern = r'pack\s*(?:de\s*)?(\d+)'
            
            # Buscar coincidencias
            kg_match = re.search(kg_pattern, text_to_analyze)
            g_match = re.search(g_pattern, text_to_analyze)
            l_match = re.search(l_pattern, text_to_analyze)
            ml_match = re.search(ml_pattern, text_to_analyze)
            unidad_match = re.search(unidad_pattern, text_to_analyze)
            pack_match = re.search(pack_pattern, text_to_analyze)
            
            if kg_match:
                quantity = float(kg_match.group(1))
                return price / quantity, quantity, 'kg'
            elif g_match:
                quantity = float(g_match.group(1)) / 1000  # convertir a kg
                return price / quantity, quantity * 1000, 'g'
            elif l_match:
                quantity = float(l_match.group(1))
                return price / quantity, quantity, 'l'
            elif ml_match:
                quantity = float(ml_match.group(1)) / 1000  # convertir a litros
                return price / quantity, quantity * 1000, 'ml'
            elif pack_match:
                quantity = int(pack_match.group(1))
                return price / quantity, quantity, 'pack'
            elif unidad_match:
                quantity = int(unidad_match.group(1))
                return price / quantity, quantity, 'unidad'
            else:
                # Si no se encuentra unidad específica, asumir 1 unidad
                return price, 1.0, 'unidad'
                
        except Exception as e:
            self.logger.error(f"Error calculando datos de unidad: {e}")
            return price, 1.0, 'unidad'

    async def await_products_loaded(self, page: Page):
        """Esperar a que los productos se carguen completamente"""
        try:
            # Verificar si la página sigue activa
            if page.is_closed():
                self.logger.error("❌ Página cerrada prematuramente")
                return
            
            # Esperar a que aparezcan los productos con timeout más largo
            await page.wait_for_selector(plaza_vea.SELECTOR_PRODUCTS_CONTAINER, timeout=30000)
            
            # Hacer scroll para cargar productos dinámicos
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
            # Esperar un poco más para asegurar carga completa
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Timeout o error esperando productos: {e}")
            # No lanzar excepción, solo continuar

    async def go_to_next_page(self, page: Page, scrapy_selector):
        """Navegar a la siguiente página si existe"""
        try:
            # Verificar si la página sigue activa
            if page.is_closed():
                self.logger.error("❌ Página cerrada, no se puede navegar")
                return False
            
            # Buscar paginación usando los XPaths corregidos
            pagination_element = scrapy_selector.xpath(plaza_vea.XPATH_PAGINATION).get()
            if not pagination_element:
                self.logger.info("📄 No se encontró elemento de paginación")
                return False
            
            # Encontrar página activa con el XPath corregido
            active_page_list = scrapy_selector.xpath(plaza_vea.XPATH_ACTIVE_PAGE).getall()
            if not active_page_list:
                self.logger.info("📄 No se encontró página activa")
                return False
            
            current_page = int(active_page_list[0])
            self.logger.info(f"📄 Página actual: {current_page}")
            
            # Obtener todas las páginas disponibles
            all_pages = scrapy_selector.xpath(plaza_vea.XPATH_ALL_PAGES).getall()
            all_page_numbers = [int(p) for p in all_pages if p.isdigit()]
            max_page = max(all_page_numbers) if all_page_numbers else current_page
            
            self.logger.info(f"📄 Páginas disponibles: {sorted(all_page_numbers)}, Máxima: {max_page}")
            
            # Verificar si hay siguiente página
            if current_page >= max_page:
                self.logger.info(f"📄 Ya estamos en la última página ({current_page}/{max_page})")
                return False
            
            next_page_number = current_page + 1
            
            # Buscar el botón de la siguiente página usando múltiples estrategias
            next_page_selectors = [
                # Estrategia 1: Buscar span con el número específico de la página siguiente
                f'//div[@class="pagination"]//span[contains(@class, "pagination__item") and contains(@class, "page-number") and not(contains(@class, "active")) and text()="{next_page_number}"]',
                
                # Estrategia 2: Buscar cualquier página mayor a la actual
                f'//div[@class="pagination"]//span[contains(@class, "pagination__item") and contains(@class, "page-number") and not(contains(@class, "active"))][1]',
                
                # Estrategia 3: Buscar botón "Siguiente" genérico
                '//div[@class="pagination"]//a[contains(@class, "next") or contains(text(), "Siguiente")]',
                '//div[@class="pagination"]//button[contains(@class, "next") or contains(text(), "Siguiente")]'
            ]
            
            next_page_element = None
            used_selector = None
            
            for selector in next_page_selectors:
                try:
                    self.logger.debug(f"🔍 Probando selector: {selector}")
                    next_page_element = await page.query_selector(f'xpath={selector}')
                    if next_page_element:
                        used_selector = selector
                        self.logger.info(f"✅ Encontrado botón siguiente con selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"❌ Selector falló: {selector} - {e}")
                    continue
            
            if next_page_element:
                # Hacer scroll para asegurar que el elemento esté visible
                await next_page_element.scroll_into_view_if_needed()
                await page.wait_for_timeout(2000)  # Esperar que termine el scroll
                
                # Hacer clic en la siguiente página
                self.logger.info(f"🔄 Haciendo clic para navegar a página {next_page_number}")
                await next_page_element.click()
                
                # Esperar a que se cargue la nueva página
                await page.wait_for_timeout(4000)  # Tiempo más generoso para carga
                
                # Verificar que efectivamente cambió de página
                await self.await_products_loaded(page)
                
                # Obtener contenido actualizado para verificar cambio
                new_html = await page.content()
                new_selector = scrapy.Selector(text=new_html)
                new_active_page = new_selector.xpath(plaza_vea.XPATH_ACTIVE_PAGE).getall()
                
                if new_active_page and int(new_active_page[0]) == next_page_number:
                    self.logger.info(f"✅ Navegación exitosa a página {new_active_page[0]}")
                    return True
                else:
                    self.logger.warning(f"⚠️ No se detectó cambio correcto de página. Esperado: {next_page_number}, Obtenido: {new_active_page}")
                    return False
                
            else:
                self.logger.info("📄 No se encontró botón para la siguiente página")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error navegando a siguiente página: {e}")
            import traceback
            traceback.print_exc()
            return False