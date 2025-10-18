import re
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scrapy.http import Response
from playwright.async_api import Page
import time

from .constants import inkafarma

class InkafarmaSpider(scrapy.Spider):
    name = "inkafarma"
    allowed_domains = ["inkafarma.pe"]
    
    def __init__(self, custom_urls=None, *args, **kwargs):
        super(InkafarmaSpider, self).__init__(*args, **kwargs)
        self.custom_urls = custom_urls  # Initialize custom_urls

        # Procesar URLs de entrada
        self.start_urls, self.subcategories = self._process_input_urls(custom_urls)
    
    def _process_input_urls(self, custom_urls):
        if custom_urls:
            urls = custom_urls.split(',') if isinstance(custom_urls, str) else custom_urls
            cleaned_urls = [url.strip() for url in urls]
            self.logger.info(f"Usando URLs personalizadas: {len(cleaned_urls)} URLs")
            return cleaned_urls, [None] * len(cleaned_urls)  # Return None for subcategories
        else:
            urls = []
            subcategories = []
            for categoria in inkafarma.CATEGORIAS:
                url = inkafarma.CATEGORIA_URL_TEMPLATE.format(categoria=categoria)
                urls.append(url)
                subcategories.append(categoria)
            self.logger.info(f"URLs generadas automáticamente: {len(urls)} URLs")
            return urls, subcategories

    def start_requests(self):
        """Generar requests iniciales con configuración de Playwright"""
        self.logger.info("🚀 Iniciando scraping de InkaFarma con Playwright...")

        urls, subcategories = self._process_input_urls(self.custom_urls)
        for i, (url, subcategory) in enumerate(zip(urls, subcategories)):
            unique_url = f"{url}?scrapy_index={i}&ts={int(time.time())}"
            yield scrapy.Request(
                url=unique_url,
                callback=self.parse_category,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "subcategory": subcategory,  # Pass subcategory in meta
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",  # Solo esperar DOM, no todos los recursos
                        "timeout": 30000,
                    },
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("wait_for_timeout", 5000),
                    ],
                },
                dont_filter=True
            )

    async def parse_category(self, response):
        """Parsea una categoría específica con scroll infinito"""
        page = response.meta["playwright_page"]
        
        try:
            # Obtener la URL actual
            current_url = page.url
            self.logger.info(f"🚀 Procesando categoría: {current_url}")
            
            # Esperar a que se carguen los productos iniciales
            await self.await_products_loaded(page)
            
            # Realizar scroll infinito para cargar TODOS los productos
            productos_cargados = await self.scroll_to_load_all_products(page)
            self.logger.info(f"✅ Total productos cargados: {productos_cargados}")
            
            # Obtener el HTML actualizado después del scroll
            content = await page.content()
            
            # Cerrar la página
            await page.close()
            
            # Crear una nueva response con el contenido completo
            from scrapy.http import HtmlResponse
            updated_response = HtmlResponse(
                url=response.url,
                body=content,
                encoding='utf-8'
            )
            
            # Parsear todos los productos
            for item in self.parse_products(updated_response):
                yield item
                
        except Exception as e:
            self.logger.error(f"❌ Error al procesar categoría {current_url}: {e}")
            if 'page' in locals():
                await page.close()

    async def await_products_loaded(self, page):
        try:
            # Esperar a que aparezcan los productos iniciales con timeout mínimo
            await page.wait_for_selector(inkafarma.SELECTOR_PRODUCTO_CARD, timeout=8000)
            self.logger.info("✅ Productos iniciales cargados")
            
            # Esperar tiempo mínimo para asegurar renderizado completo
            await page.wait_for_timeout(1500)
            
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudieron cargar productos iniciales: {e}")
            # Esperar tiempo mínimo y continuar
            await page.wait_for_timeout(2000)

    async def scroll_to_load_all_products(self, page):
        previous_height = -1
        scroll_attempts = 0
        max_attempts = 50
        
        while scroll_attempts < max_attempts:
            try:
                # Esperar a que el contenedor de productos esté completamente renderizado (timeout mínimo)
                await page.wait_for_selector(inkafarma.SELECTOR_PRODUCTOS_CONTAINER, timeout=5000)
                
                # Obtener la altura actual del contenedor de productos
                current_height = await page.evaluate(f"document.querySelector('{inkafarma.SELECTOR_PRODUCTOS_CONTAINER}').scrollHeight")
                
                self.logger.info(f"📏 Scroll {scroll_attempts + 1}: Altura del contenedor: {current_height}px")
                
                # Si la altura no cambió, significa que no hay más productos que cargar
                if current_height == previous_height:
                    self.logger.info("🛑 La altura del contenedor se estabilizó. Scroll finalizado.")
                    break
                
                previous_height = current_height
                
                # Hacer scroll hasta el final de la página actual
                self.logger.info("📜 Haciendo scroll hasta el final...")
                await page.evaluate(f"window.scrollTo(0, {current_height})")
                # Reducir tiempo de espera entre scrolls (mínimo necesario)
                await page.wait_for_timeout(1500)
                scroll_attempts += 1
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error durante scroll {scroll_attempts + 1}: {e}")
                # Si falla el contenedor, intentar scroll básico
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                scroll_attempts += 1
        
        # Obtener el conteo final de productos
        productos_finales = await page.locator(inkafarma.SELECTOR_PRODUCTO_CARD).count()
        self.logger.info(f"🏁 Scroll finalizado después de {scroll_attempts} intentos: {productos_finales} productos cargados")
        return productos_finales

    def parse_products(self, response):
        """
        Extrae productos ÚNICAMENTE después de que el scroll se haya completado y la página esté estable.
        Utiliza el selector correcto: //fp-filtered-product-list//fp-product-large (Card de producto)
        """
        # Usar XPath para seleccionar todos los fp-product-large dentro de fp-filtered-product-list
        productos = response.xpath("//fp-filtered-product-list//fp-product-large")
        
        self.logger.info(f"🔍 Procesando {len(productos)} productos encontrados (DESPUÉS del scroll completo)")
        
        for i, producto in enumerate(productos):
            try:
                item = ScraperItem()
                
                # Extraer nombre del producto
                nombre_elem = producto.css(inkafarma.SELECTOR_PRODUCTO_NOMBRE + "::text").get()
                nombre = nombre_elem.strip() if nombre_elem else ""
                
                # Extraer presentación/cantidad  
                presentacion_elem = producto.css(inkafarma.SELECTOR_PRODUCTO_PRESENTACION + "::text").get()
                presentacion = presentacion_elem.strip() if presentacion_elem else ""
                
                # Crear nombre completo como solicita el usuario: "Nombre - Presentación"
                if nombre and presentacion:
                    nombre_completo = f"{nombre} - {presentacion}"
                else:
                    nombre_completo = nombre or "Sin nombre"
                
                item['name'] = nombre_completo
                
                # Extraer precio
                precio_elem = producto.css(inkafarma.SELECTOR_PRODUCTO_PRECIO + "::text").get()
                precio_text = precio_elem.strip() if precio_elem else "0"
                
                # Limpiar y procesar precio (puede venir como "S/ 5.20S/ 2.20")
                # Separar precios múltiples y tomar el precio más bajo (oferta)
                precios = []
                if 'S/' in precio_text:
                    # Dividir por 'S/' y limpiar cada precio
                    partes = precio_text.split('S/')
                    for parte in partes:
                        if parte.strip():
                            # Remover todo excepto números y punto decimal
                            precio_limpio = inkafarma.REGEX_SOLO_NUMEROS.sub('', parte.strip())
                            try:
                                if precio_limpio:
                                    precios.append(float(precio_limpio))
                            except ValueError:
                                continue
                
                # Tomar el precio más bajo (generalmente el precio de oferta)
                precio = min(precios) if precios else 0.0
                
                item['price'] = precio
                
                # Calcular precio unitario basado en la presentación
                unit_price = self.calculate_unit_price(precio, presentacion)
                item['unit_price'] = unit_price
                
                # Extraer cantidad y unidad de la presentación
                quantity, unit_type = self.extract_quantity_and_unit(presentacion)
                item['total_unit_quantity'] = quantity
                item['unit_type'] = unit_type
                
                item['category'] = "Farmacia"
                
                # Información comercial
                item['comercial_name'] = inkafarma.COMERCIAL_NAME
                item['comercial_id'] = inkafarma.COMERCIAL_ID
                
                yield item
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando producto {i+1}: {e}")
                continue
        
        self.logger.info(f"✅ Scraping completado: {len(productos)} productos extraídos (después del scroll completo)")
    
    def calculate_unit_price(self, precio_total, presentacion):
        try:
            match = inkafarma.REGEX_CANTIDAD_PRESENTACION.search(presentacion)
            if match:
                cantidad = float(match.group(1))
                if cantidad > 0:
                    return round(precio_total / cantidad, 2)
            return precio_total
        except Exception:
            return precio_total
    
    def extract_quantity_and_unit(self, presentacion):
        """Extrae cantidad y unidad de la presentación"""
        try:
            match = inkafarma.REGEX_CANTIDAD_PRESENTACION.search(presentacion)
            if match:
                cantidad = float(match.group(1))
                unidad = match.group(2).lower()
                return cantidad, unidad
            # Si no encuentra patrón específico, asumir 1 unidad
            return 1.0, "un"
        except Exception:
            return 1.0, "un"
    
    def extract_category_from_url(self, url):
        """Extrae la categoría desde la URL"""
        try:
            # URL format: https://inkafarma.pe/categoria/categoria-nombre
            if '/categoria/' in url:
                categoria = url.split('/categoria/')[-1]
                return categoria.replace('-', ' ').title()
            return "General"
        except Exception:
            return "General"