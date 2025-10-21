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

    async def extract_menu_structure(self, page, category_prefix):
        """
        Extrae la estructura del menú de InkaFarma usando una estrategia directa.
        En lugar de depender del hover, usa las categorías conocidas de InkaFarma.
        """
        menu_structure = {}

        try:
            # Usar categorías directas ya que el hover no funciona como esperábamos
            target_dept_url = f"https://inkafarma.pe/categoria/{category_prefix}"
            
            self.logger.info(f"🚀 Navegando directamente al departamento: {target_dept_url}")
            await page.goto(target_dept_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Verificar si la página cargó correctamente
            page_title = await page.title()
            if "404" in page_title or "Not Found" in page_title:
                self.logger.warning(f"⚠️ Categoría no encontrada: {target_dept_url}")
                return {}
            
            # Verificar si esta página tiene subcategorías o productos directamente
            product_count = await self.get_product_count(page)
            self.logger.info(f"📊 Productos en departamento '{category_prefix}': {product_count}")
            
            if product_count >= 250:
                # Buscar subcategorías en filtros laterales o en la página
                self.logger.info("🔍 Buscando subcategorías...")
                
                # Estrategia 1: Buscar enlaces de subcategorías en filtros
                subcategory_links = await page.query_selector_all("a[href*='/categoria/']")
                categorias_data = []
                seen_urls = set()
                
                for subcat_link in subcategory_links:
                    href = await subcat_link.get_attribute("href")
                    text = await subcat_link.text_content()
                    
                    if href and href != f"/categoria/{category_prefix}" and category_prefix in href:
                        # Evitar duplicados
                        if href not in seen_urls:
                            seen_urls.add(href)
                            full_url = f"https://inkafarma.pe{href}" if href.startswith('/') else href
                            categorias_data.append({
                                "nombre": text.strip() if text else f"Subcategoría {len(categorias_data)+1}",
                                "href": full_url,
                                "subcategorias": []
                            })
                self.logger.info(f"📋 Encontradas {len(categorias_data)} subcategorías para '{category_prefix}'")
                
                if len(categorias_data) == 0:
                    self.logger.warning(f"⚠️ No se encontraron subcategorías válidas para '{category_prefix}'. Activando fallback...")
                    return {}  # Estructura vacía para activar fallback
                
                menu_structure = {
                    "departamento": {
                        "nombre": category_prefix.replace("-", " ").title(),
                        "href": target_dept_url
                    },
                    "categorias": categorias_data
                }
            else:
                # Si tiene pocos productos, extraer directamente
                self.logger.info(f"✅ Departamento '{category_prefix}' tiene {product_count} productos. Extrayendo directamente...")
                menu_structure = {
                    "departamento": {
                        "nombre": category_prefix.replace("-", " ").title(),
                        "href": target_dept_url
                    },
                    "categorias": [],
                    "extract_direct": True
                }

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo estructura del menú para '{category_prefix}': {e}")
            import traceback
            self.logger.error(f"🔍 Traceback: {traceback.format_exc()}")

        return menu_structure

    async def parse_category(self, response):
        """Parsea una categoría específica - si >= 250 productos, extrae del menú y navega directamente"""
        page = response.meta["playwright_page"]
        
        try:
            current_url = page.url
            self.logger.info(f"🚀 Procesando categoría: {current_url}")
            
            # Esperar a que se cargue la página inicial
            await page.wait_for_timeout(3000)

            # Verificar el número de productos en la página
            product_count = await self.get_product_count(page)
            self.logger.info(f"📊 Productos encontrados en la categoría: {product_count}")

            if product_count < 250:
                # Si hay menos de 250 productos, hacer scroll e extraer
                self.logger.info(f"✅ {product_count} productos (<250). Extrayendo directamente...")
                await self.await_products_loaded(page)
                productos_cargados = await self.scroll_to_load_all_products(page)
                self.logger.info(f"✅ Total productos cargados: {productos_cargados}")
                content = await page.content()
                await page.close()
                from scrapy.http import HtmlResponse
                updated_response = HtmlResponse(
                    url=response.url,
                    body=content,
                    encoding='utf-8'
                )
                for item in self.parse_products(updated_response):
                    yield item
            else:
                # Si hay >= 250 productos, extraer URLs del menú y navegar a subcategorías
                self.logger.info(f"🔄 Detectados {product_count} productos (>=250). Buscando subcategorías en el menú...")
                
                category_name = self.extract_category_from_url(current_url)
                category_prefix = category_name[:4].lower()
                self.logger.info(f"🔍 Buscando departamento que empiece con: '{category_prefix}'")
                
                # Extraer toda la estructura del menú
                menu_structure = await self.extract_menu_structure(page, category_prefix)
                
                if not menu_structure or not menu_structure.get('categorias'):
                    self.logger.warning("⚠️ No se encontró estructura del menú o departamentos. Haciendo fallback a scraping directo...")
                    
                    # FALLBACK: Volver a la URL original y hacer scraping directo
                    original_url = response.url.split('?')[0]  # Remover parámetros de scrapy
                    self.logger.info(f"🔄 Fallback: Navegando de vuelta a la URL original: {original_url}")
                    
                    try:
                        await page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(3000)
                        
                        # Hacer scraping directo con scroll infinito
                        self.logger.info("📜 Fallback: Iniciando scraping directo con scroll infinito...")
                        await self.await_products_loaded(page)
                        productos_cargados = await self.scroll_to_load_all_products(page)
                        self.logger.info(f"✅ Fallback completado: {productos_cargados} productos extraídos")
                        
                        content = await page.content()
                        from scrapy.http import HtmlResponse
                        updated_response = HtmlResponse(
                            url=original_url,
                            body=content,
                            encoding='utf-8'
                        )
                        for item in self.parse_products(updated_response):
                            yield item
                            
                    except Exception as fallback_error:
                        self.logger.error(f"❌ Error en fallback: {fallback_error}")
                    
                    await page.close()
                    return
                
                # Procesar cada categoría del array temporal
                categorias = menu_structure.get('categorias', [])
                self.logger.info(f"📋 Procesando {len(categorias)} categorías del menú...")
                
                for cat_info in categorias:
                    cat_nombre = cat_info.get('nombre', 'Sin nombre')
                    cat_href = cat_info.get('href', '')
                    subcategorias = cat_info.get('subcategorias', [])
                    
                    self.logger.info(f"🔄 Procesando categoría: '{cat_nombre}'")
                    
                    if subcategorias:
                        # Si hay subcategorías, procesar cada una
                        self.logger.info(f"  📊 Encontradas {len(subcategorias)} subcategorías")
                        
                        for subcat_info in subcategorias:
                            subcat_nombre = subcat_info.get('nombre', 'Sin nombre')
                            subcat_href = subcat_info.get('href', '')
                            
                            if not subcat_href:
                                self.logger.warning(f"  ⚠️ Subcategoría sin href: {subcat_nombre}")
                                continue
                            
                            # Navegar a la subcategoría
                            full_url = f"https://inkafarma.pe{subcat_href}" if subcat_href.startswith('/') else subcat_href
                            self.logger.info(f"  ➡️ Navegando a subcategoría: '{subcat_nombre}' → {full_url}")
                            
                            try:
                                await page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                                await page.wait_for_timeout(2000)
                                
                                # Verificar productos en esta subcategoría
                                subcat_count = await self.get_product_count(page)
                                self.logger.info(f"  📊 Productos en '{subcat_nombre}': {subcat_count}")
                                
                                if subcat_count > 0:
                                    # Extraer productos
                                    await self.await_products_loaded(page)
                                    productos_cargados = await self.scroll_to_load_all_products(page)
                                    self.logger.info(f"  ✅ Productos extraídos: {productos_cargados}")
                                    
                                    content = await page.content()
                                    from scrapy.http import HtmlResponse
                                    updated_response = HtmlResponse(
                                        url=page.url,
                                        body=content,
                                        encoding='utf-8'
                                    )
                                    for item in self.parse_products(updated_response, subcat_nombre):
                                        yield item
                                
                            except Exception as e:
                                self.logger.error(f"  ❌ Error procesando subcategoría '{subcat_nombre}': {e}")
                                continue
                    else:
                        # Si no hay subcategorías, procesar la categoría directamente
                        if not cat_href:
                            self.logger.warning(f"  ⚠️ Categoría sin href: {cat_nombre}")
                            continue
                        
                        full_url = f"https://inkafarma.pe{cat_href}" if cat_href.startswith('/') else cat_href
                        self.logger.info(f"  ➡️ Navegando a categoría: '{cat_nombre}' → {full_url}")
                        
                        try:
                            await page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_timeout(2000)
                            
                            cat_count = await self.get_product_count(page)
                            self.logger.info(f"  📊 Productos en '{cat_nombre}': {cat_count}")
                            
                            if cat_count > 0:
                                await self.await_products_loaded(page)
                                productos_cargados = await self.scroll_to_load_all_products(page)
                                self.logger.info(f"  ✅ Productos extraídos: {productos_cargados}")
                                
                                content = await page.content()
                                from scrapy.http import HtmlResponse
                                updated_response = HtmlResponse(
                                    url=page.url,
                                    body=content,
                                    encoding='utf-8'
                                )
                                for item in self.parse_products(updated_response, cat_nombre):
                                    yield item
                        
                        except Exception as e:
                            self.logger.error(f"  ❌ Error procesando categoría '{cat_nombre}': {e}")
                            continue
                
                await page.close()

        except Exception as e:
            self.logger.error(f"❌ Error al procesar categoría: {e}")
            if 'page' in locals():
                await page.close()

    async def get_product_count(self, page):
        """Obtener el número de productos de la página usando el selector h3"""
        import re
        try:
            await page.wait_for_selector(inkafarma.SELECTOR_PRODUCT_COUNT_H3, timeout=3000)
            count_text = await page.text_content(inkafarma.SELECTOR_PRODUCT_COUNT_H3)
            match = re.search(r'(\d+)', count_text)
            if match:
                count = int(match.group(1))
                self.logger.info(f"📝 Encontrado en h3: {count} productos")
                return count
        except Exception as e:
            self.logger.warning(f"⚠️ No se encontró h3 de conteo: {e}")
        self.logger.warning("⚠️ No se pudo obtener el conteo de productos")
        return 0

    async def navigate_subcategories(self, page, current_url):
        """Navegar por subcategorías cuando hay >= 250 productos usando los selectores actualizados"""
        try:
            category_name = self.extract_category_from_url(current_url)
            category_prefix = category_name[:4].lower()
            self.logger.info(f"🔍 Buscando subcategorías que contengan: {category_prefix}")

            # Hacer clic en el menú de categorías
            await page.click(inkafarma.SELECTOR_CATEGORIES_MENU_BUTTON)
            await page.wait_for_timeout(2000)

            # Buscar subcategorías
            subcategory_elements = await page.query_selector_all(inkafarma.SELECTOR_SUBCATEGORIES)
            self.logger.info(f"📂 Encontradas {len(subcategory_elements)} subcategorías")

            for i, subcat in enumerate(subcategory_elements):
                # Obtener el texto del span dentro de la subcategoría
                span = await subcat.query_selector(inkafarma.SELECTOR_SUBCATEGORY_SPAN)
                subcat_text = await span.text_content() if span else ""
                self.logger.info(f"🔄 Subcategoría {i+1}: {subcat_text}")
                # Verificar si el texto contiene el prefijo de la categoría
                if category_prefix in subcat_text.lower():
                    self.logger.info(f"✅ Subcategoría relevante encontrada: {subcat_text}")
                    # Hacer clic en la subcategoría
                    await subcat.click()
                    await page.wait_for_timeout(2000)
                    # Esperar a que se carguen los productos iniciales
                    await self.await_products_loaded(page)
                    # Realizar scroll infinito para cargar TODOS los productos
                    productos_cargados = await self.scroll_to_load_all_products(page)
                    self.logger.info(f"✅ Total productos cargados en subcategoría '{subcat_text}': {productos_cargados}")
                    # Obtener el HTML actualizado después del scroll
                    content = await page.content()
                    from scrapy.http import HtmlResponse
                    updated_response = HtmlResponse(
                        url=page.url,
                        body=content,
                        encoding='utf-8'
                    )
                    # Parsear todos los productos
                    for item in self.parse_products(updated_response, subcat_text):
                        yield item
                    # Volver al menú para la siguiente subcategoría
                    await page.click(inkafarma.SELECTOR_CATEGORIES_MENU_BUTTON)
                    await page.wait_for_timeout(1000)
            # Si no se encuentra ninguna subcategoría relevante, loggear
            self.logger.info("🔍 Procesamiento de subcategorías completado")
        except Exception as e:
            self.logger.error(f"❌ Error navegando subcategorías: {e}")
            self.logger.info("🔄 Navegación de subcategorías falló, continuando con scraping normal...")
            await self.await_products_loaded(page)
            productos_cargados = await self.scroll_to_load_all_products(page)
            self.logger.info(f"✅ Scraping normal completado: {productos_cargados} productos cargados")
            content = await page.content()
            from scrapy.http import HtmlResponse
            updated_response = HtmlResponse(
                url=str(page.url),
                body=content,
                encoding='utf-8'
            )
            for item in self.parse_products(updated_response, None):
                yield item

    async def process_subcategory_products(self, page, subcategory_name):
        """Procesar productos de una subcategoría específica"""
        try:
            # Verificar si esta subcategoría también tiene >= 250 productos
            subcategory_count = await self.get_product_count(page)
            self.logger.info(f"📊 Subcategoría '{subcategory_name}': {subcategory_count} productos")
            
            if subcategory_count >= 250:
                # Si la subcategoría también tiene muchos productos, podría tener sub-subcategorías
                # Por ahora, procesamos normalmente pero se puede extender recursivamente
                self.logger.warning(f"⚠️ Subcategoría '{subcategory_name}' tiene {subcategory_count} productos (>=250)")
            
            # Esperar a que se carguen los productos
            await self.await_products_loaded(page)
            
            # Realizar scroll para cargar todos los productos
            productos_cargados = await self.scroll_to_load_all_products(page)
            self.logger.info(f"✅ Subcategoría '{subcategory_name}': {productos_cargados} productos cargados")
            
            # Obtener el HTML y procesar productos
            content = await page.content()
            from scrapy.http import HtmlResponse
            updated_response = HtmlResponse(
                url=page.url,
                body=content,
                encoding='utf-8'
            )
            
            # Parsear productos con la subcategoría como contexto
            for item in self.parse_products(updated_response, subcategory_name):
                yield item
                
        except Exception as e:
            self.logger.error(f"❌ Error procesando productos de subcategoría '{subcategory_name}': {e}")

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
        max_attempts = 55
        stable_attempts = 0
        max_stable_attempts = 3
        
        while scroll_attempts < max_attempts:
            try:
                # Obtener la altura actual del contenedor de productos (sin esperar al selector)
                current_height = await page.evaluate(f"""
                    (() => {{
                        const container = document.querySelector('{inkafarma.SELECTOR_PRODUCTOS_CONTAINER}');
                        return container ? container.scrollHeight : document.body.scrollHeight;
                    }})()
                """)
                
                self.logger.info(f"📏 Scroll {scroll_attempts + 1}: Altura del contenedor: {current_height}px")
                
                # Si la altura no cambió, verificar estabilidad
                if current_height == previous_height:
                    stable_attempts += 1
                    self.logger.info(f"🔄 Altura estable {stable_attempts}/{max_stable_attempts}")
                    
                    if stable_attempts >= max_stable_attempts:
                        self.logger.info("🛑 La altura del contenedor se estabilizó completamente. Scroll finalizado.")
                        break
                else:
                    # Si cambió la altura, resetear contador de estabilidad
                    stable_attempts = 0
                
                previous_height = current_height
                
                # Hacer scroll hasta el final de la página actual
                self.logger.info("📜 Haciendo scroll hasta el final...")
                await page.evaluate(f"window.scrollTo(0, {current_height})")
                
                # Esperar tiempo reducido entre scrolls
                await page.wait_for_timeout(1000)
                scroll_attempts += 1
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error durante scroll {scroll_attempts + 1}: {e}")
                # Si falla el contenedor, intentar scroll básico
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                scroll_attempts += 1
        
        # Obtener el conteo final de productos solo después de que el tamaño se estabilice
        try:
            productos_finales = await page.locator(inkafarma.SELECTOR_PRODUCTO_CARD).count()
            self.logger.info(f"🏁 Scroll finalizado después de {scroll_attempts} intentos: {productos_finales} productos cargados")
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo conteo final de productos: {e}")
            productos_finales = 0
        
        return productos_finales

    def parse_products(self, response, subcategory_name=None):
        """
        Extrae productos ÚNICAMENTE después de que el scroll se haya completado y la página esté estable.
        Utiliza el selector correcto: //fp-filtered-product-list//fp-product-large (Card de producto)
        """
        # Usar XPath para seleccionar todos los fp-product-large dentro de fp-filtered-product-list
        productos = response.xpath("//fp-filtered-product-list//fp-product-large")
        
        context = f" en subcategoría '{subcategory_name}'" if subcategory_name else ""
        self.logger.info(f"🔍 Procesando {len(productos)} productos encontrados{context} (DESPUÉS del scroll completo)")
        
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
                
                # Usar subcategoría si está disponible, sino categoría general
                item['category'] = subcategory_name if subcategory_name else "Farmacia"
                
                # Información comercial
                item['comercial_name'] = inkafarma.COMERCIAL_NAME
                item['comercial_id'] = inkafarma.COMERCIAL_ID
                
                yield item
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando producto {i+1}: {e}")
                continue
        
        self.logger.info(f"✅ Scraping completado: {len(productos)} productos extraídos{context} (después del scroll completo)")
    
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