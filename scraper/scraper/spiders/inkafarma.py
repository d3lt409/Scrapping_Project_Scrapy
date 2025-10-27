import re
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scrapy.http import Response
from playwright.async_api import Page
import time
import json
import os
import subprocess
from datetime import datetime, timedelta

from .constants import inkafarma

class InkafarmaSpider(scrapy.Spider):
    name = "inkafarma"
    allowed_domains = ["inkafarma.pe"]
    
    def __init__(self, custom_urls=None, *args, **kwargs):
        super(InkafarmaSpider, self).__init__(*args, **kwargs)
        self.custom_urls = custom_urls  # Initialize custom_urls
        
        # Cargar o actualizar la estructura JSON
        self.structure_data = self._load_or_update_structure()
        
        # Procesar URLs de entrada basándose en la estructura JSON
        self.start_urls = self._process_json_structure()
    
    def _get_json_path(self):
        """Obtiene la ruta del archivo JSON de estructura"""
        return os.path.join(os.path.dirname(__file__), "constants", "inkafarma_complete_structure.json")
    
    def _is_json_outdated(self):
        """Verifica si el JSON es mayor a 1 mes de antigüedad"""
        json_path = self._get_json_path()
        
        if not os.path.exists(json_path):
            self.logger.info("📋 Archivo JSON no existe, necesita generarse")
            return True
        
        # Obtener fecha de modificación del archivo
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(json_path))
        one_month_ago = datetime.now() - timedelta(days=30)
        
        if file_mod_time < one_month_ago:
            self.logger.info(f"⏰ Archivo JSON desactualizado. Última modificación: {file_mod_time}")
            return True
        
        self.logger.info(f"✅ Archivo JSON actualizado. Última modificación: {file_mod_time}")
        return False
    
    def _run_inkatest_spider(self):
        """Ejecuta el spider inkatest para generar/actualizar el JSON"""
        try:
            self.logger.info("🚀 Ejecutando spider inkatest para actualizar estructura...")
            
            # Cambiar al directorio del proyecto para ejecutar scrapy
            current_dir = os.getcwd()
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            os.chdir(project_dir)
            
            # Ejecutar el spider inkatest
            result = subprocess.run(
                ["scrapy", "crawl", "inkatest"],
                capture_output=True,
                text=True,
                timeout=7200  # 2 horas máximo
            )
            
            os.chdir(current_dir)
            
            if result.returncode == 0:
                self.logger.info("✅ Spider inkatest completado exitosamente")
                return True
            else:
                self.logger.error(f"❌ Error ejecutando inkatest: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Timeout ejecutando inkatest")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando inkatest: {e}")
            return False
    
    def _load_structure_json(self):
        """Carga la estructura desde el archivo JSON"""
        json_path = self._get_json_path()
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"📊 Estructura cargada: {data['metadata']['total_categories']} categorías, "
                           f"{data['metadata']['total_subcategories']} subcategorías, "
                           f"{data['metadata']['total_subsubcategories']} sub-subcategorías")
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando JSON: {e}")
            return None
    
    def _load_or_update_structure(self):
        """Carga la estructura JSON o la actualiza si es necesario"""
        
        # Verificar si necesita actualización
        if self._is_json_outdated():
            self.logger.info("🔄 Actualizando estructura de categorías...")
            
            if self._run_inkatest_spider():
                self.logger.info("✅ Estructura actualizada exitosamente")
            else:
                self.logger.warning("⚠️ No se pudo actualizar, usando estructura existente")
        
        # Cargar la estructura (actualizada o existente)
        return self._load_structure_json()
    
    def _process_json_structure(self):
        """Procesa la estructura JSON para generar URLs de inicio"""
        if not self.structure_data:
            self.logger.error("❌ No hay estructura JSON disponible, usando fallback")
            return ["https://inkafarma.pe/"]
        
        # Si hay custom_urls, usarlas
        if self.custom_urls:
            urls = self.custom_urls.split(',') if isinstance(self.custom_urls, str) else self.custom_urls
            return [url.strip() for url in urls]
        
        # Generar URLs desde el JSON
        start_urls = []
        
        for category_key, category_data in self.structure_data["categories"].items():
            # Agregar URL de la categoría principal
            category_url = f"https://inkafarma.pe{category_data['href']}"
            start_urls.append(category_url)
        
        self.logger.info(f"🎯 Generadas {len(start_urls)} URLs desde estructura JSON")
        return start_urls
    
    def _extract_category_info_from_url(self, url):
        """Extrae información de categoría desde la URL usando la estructura JSON"""
        if not self.structure_data:
            return None
        
        # Extraer path de la URL
        path = url.replace("https://inkafarma.pe", "")
        
        # Buscar en la estructura JSON
        for category_key, category_data in self.structure_data["categories"].items():
            if category_data["href"] == path:
                return {
                    "level": "category",
                    "category_key": category_key,
                    "category_name": category_data["name"],
                    "href": category_data["href"],
                    "subcategories": category_data["subcategories"]
                }
        
        return None
    
    def _get_subcategory_urls(self, category_info):
        """Obtiene URLs de subcategorías para una categoría dada"""
        urls = []
        
        if category_info and "subcategories" in category_info:
            for sub_key, sub_data in category_info["subcategories"].items():
                url = f"https://inkafarma.pe{sub_data['href']}"
                urls.append({
                    "url": url,
                    "category_name": category_info["category_name"],
                    "subcategory_name": sub_data["name"],
                    "subcategory_key": sub_key,
                    "href": sub_data["href"],
                    "subsubcategories": sub_data.get("subsubcategories", {})
                })
        
        return urls
    
    def _get_subsubcategory_urls(self, subcategory_info):
        """Obtiene URLs de sub-subcategorías para una subcategoría dada"""
        urls = []
        
        if "subsubcategories" in subcategory_info:
            for subsub_key, subsub_data in subcategory_info["subsubcategories"].items():
                url = f"https://inkafarma.pe{subsub_data['href']}"
                urls.append({
                    "url": url,
                    "category_name": subcategory_info["category_name"],
                    "subcategory_name": subcategory_info["subcategory_name"],
                    "subsubcategory_name": subsub_data["name"],
                    "href": subsub_data["href"]
                })
        
        return urls
    
    async def _count_products_on_page(self, page):
        """Cuenta los productos en la página actual usando el H3 que muestra el conteo real"""
        try:
            # Esperar a que se cargue el contenido y el H3 con el conteo
            await page.wait_for_selector(inkafarma.SELECTOR_PRODUCT_COUNT_H3, timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Obtener el texto del H3 que contiene el conteo de productos
            h3_element = page.locator(inkafarma.SELECTOR_PRODUCT_COUNT_H3)
            h3_text = await h3_element.text_content()
            
            if h3_text:
                # Extraer número usando regex (ej: "Encontramos 156 productos")
                import re
                match = re.search(r'(\d+)', h3_text)
                if match:
                    count = int(match.group(1))
                    self.logger.info(f"📊 Conteo desde H3: '{h3_text}' -> {count} productos")
                    return count
            
            # Fallback: contar elementos DOM si no se encuentra el H3
            products = page.locator("//fp-filtered-product-list//fp-product-large")
            count = await products.count()
            self.logger.warning(f"⚠️ Usando conteo DOM fallback: {count}")
            return count
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error contando productos: {e}")
            return 0
    
    async def parse_category_json(self, response):
        """Parser principal usando la estructura JSON"""
        page = response.meta["playwright_page"]
        category_info = response.meta["category_info"]
        
        if not category_info:
            self.logger.error(f"❌ No se pudo extraer información de categoría para {response.url}")
            await page.close()
            return
        
        self.logger.info(f"🔍 Procesando categoría: {category_info['category_name']}")
        
        # Contar productos en la página actual
        product_count = await self._count_products_on_page(page)
        self.logger.info(f"📊 Productos encontrados en categoría principal: {product_count}")
        
        # Si hay más de 250 productos, navegar por subcategorías
        if product_count >= 250:
            self.logger.info(f"⚠️ Categoría con {product_count} productos (≥250). Navegando por subcategorías...")
            
            # Generar requests para subcategorías
            subcategory_urls = self._get_subcategory_urls(category_info)
            
            for sub_info in subcategory_urls:
                yield scrapy.Request(
                    url=sub_info["url"],
                    callback=self.parse_subcategory_json,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "subcategory_info": sub_info,
                        "playwright_page_goto_kwargs": {
                            "wait_until": "domcontentloaded",
                            "timeout": 30000,
                        },
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("wait_for_timeout", 3000),
                        ],
                    }
                )
        else:
            # Procesar productos directamente
            async for item in self.parse_products(response, category_name="farmacia", subcategory_name=category_info['category_name']):
                yield item
        
        await page.close()
    
    async def parse_subcategory_json(self, response):
        """Parser para subcategorías usando la estructura JSON"""
        page = response.meta["playwright_page"]
        subcategory_info = response.meta["subcategory_info"]
        
        self.logger.info(f"🔍 Procesando subcategoría: {subcategory_info['subcategory_name']}")
        
        # Contar productos en la subcategoría
        product_count = await self._count_products_on_page(page)
        self.logger.info(f"📊 Productos encontrados en subcategoría: {product_count}")
        
        # Si hay más de 250 productos, navegar por sub-subcategorías
        if product_count >= 250 and subcategory_info.get("subsubcategories"):
            self.logger.info(f"⚠️ Subcategoría con {product_count} productos (≥250). Navegando por sub-subcategorías...")
            
            # Generar requests para sub-subcategorías
            subsubcategory_urls = self._get_subsubcategory_urls(subcategory_info)
            
            for subsub_info in subsubcategory_urls:
                yield scrapy.Request(
                    url=subsub_info["url"],
                    callback=self.parse_subsubcategory_json,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "subsubcategory_info": subsub_info,
                        "playwright_page_goto_kwargs": {
                            "wait_until": "domcontentloaded",
                            "timeout": 30000,
                        },
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("wait_for_timeout", 3000),
                        ],
                    }
                )
        else:
            # Procesar productos directamente
            async for item in self.parse_products(response, category_name="farmacia", subcategory_name=subcategory_info['subcategory_name']):
                yield item
        
        await page.close()
    
    async def parse_subsubcategory_json(self, response):
        """Parser para sub-subcategorías usando la estructura JSON"""
        page = response.meta["playwright_page"]
        subsubcategory_info = response.meta["subsubcategory_info"]
        
        self.logger.info(f"🔍 Procesando sub-subcategoría: {subsubcategory_info['subsubcategory_name']}")
        
        # Procesar productos directamente (nivel más profundo)
        async for item in self.parse_products(response, category_name="farmacia", subcategory_name=subsubcategory_info['subcategory_name']):
            yield item
        
        await page.close()
    
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

    def generate_all_subcategory_urls(self):
        """
        Genera todas las URLs de subcategorías usando la estructura JSON (preferred)
        Útil para scraping exhaustivo por subcategorías
        """
        all_urls = []
        # Preferir la estructura JSON si está disponible
        if self.structure_data and isinstance(self.structure_data.get('categories'), dict):
            for categoria_key, categoria_obj in self.structure_data['categories'].items():
                subcategories = categoria_obj.get('subcategories', {}) or {}
                for subcat_key, subcat_obj in subcategories.items():
                    href = subcat_obj.get('href') or f"/categoria/{categoria_key}/{subcat_key}"
                    url = f"https://inkafarma.pe{href}"
                    all_urls.append({
                        'url': url,
                        'categoria': categoria_key,
                        'subcategoria': subcat_key
                    })

            self.logger.info(f"📋 Generadas {len(all_urls)} URLs de subcategorías desde JSON")
            return all_urls

        # Fallback a constantes si por algún motivo no existe el JSON
        for categoria, subcategorias in getattr(inkafarma, 'CATEGORIAS_CON_SUBCATEGORIAS', {}).items():
            for subcategoria in subcategorias:
                url = inkafarma.CATEGORIA_SUBCATEGORIA_URL_TEMPLATE.format(
                    categoria=categoria,
                    subcategoria=subcategoria
                )
                all_urls.append({
                    'url': url,
                    'categoria': categoria,
                    'subcategoria': subcategoria
                })

        self.logger.info(f"📋 Generadas {len(all_urls)} URLs de subcategorías (fallback constantes)")
        return all_urls

    def start_requests(self):
        """Generar requests iniciales usando la estructura JSON"""
        self.logger.info("🚀 Iniciando scraping de InkaFarma con estructura JSON...")

        for i, url in enumerate(self.start_urls):
            unique_url = f"{url}?scrapy_index={i}&ts={int(time.time())}"
            
            # Extraer información de categoría desde la URL
            category_info = self._extract_category_info_from_url(url)
            
            yield scrapy.Request(
                url=unique_url,
                callback=self.parse_category_json,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "category_info": category_info,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",
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
                # Extraer categoría de la URL para usar como subcategoría
                category_name = self.extract_category_from_url(response.url)
                for item in self.parse_products(updated_response, category_name):
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
                    self.logger.warning("⚠️ No se encontró estructura del menú o departamentos. Activando fallback con subcategorías predefinidas...")
                    
                    # NUEVO FALLBACK: Usar estructura JSON (preferible) o constantes como última opción
                    category_raw = self.extract_category_raw_from_url(current_url)
                    self.logger.info(f"🔍 Buscando categoria '{category_raw}' en estructura JSON...")

                    # Intentar obtener subcategorías desde la estructura JSON
                    if self.structure_data and isinstance(self.structure_data.get('categories'), dict) and category_raw in self.structure_data['categories']:
                        subcats_data = self.structure_data['categories'][category_raw].get('subcategories', {}) or {}
                        self.logger.info(f"✅ Encontrada categoria '{category_raw}' con {len(subcats_data)} subcategorías (desde JSON)")

                        # Procesar cada subcategoría usando los href del JSON
                        for subcat_key, subcat_obj in subcats_data.items():
                            try:
                                href = subcat_obj.get('href') or f"/categoria/{category_raw}/{subcat_key}"
                                subcategoria_url = f"https://inkafarma.pe{href}"
                                self.logger.info(f"🔄 JSON Fallback: Procesando subcategoría '{subcat_key}' → {subcategoria_url}")

                                # Navegar a la subcategoría
                                await page.goto(subcategoria_url, wait_until="domcontentloaded", timeout=30000)
                                await page.wait_for_timeout(3000)

                                # Verificar si la subcategoría existe y tiene productos
                                page_title = await page.title()
                                if "404" not in page_title and "Not Found" not in page_title:
                                    subcat_count = await self.get_product_count(page)
                                    self.logger.info(f"  � Productos en subcategoría '{subcat_key}': {subcat_count}")

                                    if subcat_count > 0:
                                        # Extraer productos de la subcategoría
                                        await self.await_products_loaded(page)
                                        productos_cargados = await self.scroll_to_load_all_products(page)
                                        self.logger.info(f"  ✅ Productos extraídos de '{subcat_key}': {productos_cargados}")

                                        content = await page.content()
                                        from scrapy.http import HtmlResponse
                                        updated_response = HtmlResponse(
                                            url=subcategoria_url,
                                            body=content,
                                            encoding='utf-8'
                                        )
                                        for item in self.parse_products(updated_response, subcat_key):
                                            yield item
                                    else:
                                        self.logger.info(f"  ⚠️ Subcategoría '{subcat_key}' sin productos")
                                else:
                                    self.logger.warning(f"  ⚠️ Subcategoría no encontrada: {subcategoria_url}")

                            except Exception as subcat_error:
                                self.logger.error(f"  ❌ Error procesando subcategoría '{subcat_key}': {subcat_error}")
                                continue

                        await page.close()
                        return

                    # Si no está en JSON, intentar fallback a las constantes antiguas
                    self.logger.info(f"🔍 Intentando fallback con constantes para '{category_raw}'")
                    if hasattr(inkafarma, 'CATEGORIAS_CON_SUBCATEGORIAS') and category_raw in inkafarma.CATEGORIAS_CON_SUBCATEGORIAS:
                        subcategorias = inkafarma.CATEGORIAS_CON_SUBCATEGORIAS[category_raw]
                        self.logger.info(f"✅ Encontrada categoria '{category_raw}' con {len(subcategorias)} subcategorías (desde constantes)")

                        for subcategoria in subcategorias:
                            try:
                                subcategoria_url = inkafarma.CATEGORIA_SUBCATEGORIA_URL_TEMPLATE.format(
                                    categoria=category_raw,
                                    subcategoria=subcategoria
                                )
                                self.logger.info(f"🔄 Constantes Fallback: Procesando subcategoría '{subcategoria}' → {subcategoria_url}")

                                await page.goto(subcategoria_url, wait_until="domcontentloaded", timeout=30000)
                                await page.wait_for_timeout(3000)

                                page_title = await page.title()
                                if "404" not in page_title and "Not Found" not in page_title:
                                    subcat_count = await self.get_product_count(page)
                                    self.logger.info(f"  📊 Productos en subcategoría '{subcategoria}': {subcat_count}")

                                    if subcat_count > 0:
                                        await self.await_products_loaded(page)
                                        productos_cargados = await self.scroll_to_load_all_products(page)
                                        self.logger.info(f"  ✅ Productos extraídos de '{subcategoria}': {productos_cargados}")

                                        content = await page.content()
                                        from scrapy.http import HtmlResponse
                                        updated_response = HtmlResponse(
                                            url=subcategoria_url,
                                            body=content,
                                            encoding='utf-8'
                                        )
                                        for item in self.parse_products(updated_response, subcategoria):
                                            yield item
                                    else:
                                        self.logger.info(f"  ⚠️ Subcategoría '{subcategoria}' sin productos")
                                else:
                                    self.logger.warning(f"  ⚠️ Subcategoría no encontrada: {subcategoria_url}")

                            except Exception as subcat_error:
                                self.logger.error(f"  ❌ Error procesando subcategoría '{subcategoria}': {subcat_error}")
                                continue

                        await page.close()
                        return
                    else:
                        self.logger.warning(f"⚠️ Categoría '{category_raw}' no encontrada en estructura (JSON ni constantes)")
                        if not self.structure_data:
                            self.logger.error("❌ Estructura JSON no está disponible para el fallback")
                    
                    # FALLBACK FINAL: Si no se encuentra en la estructura, scraping directo
                    original_url = response.url.split('?')[0]  # Remover parámetros de scrapy
                    self.logger.info(f"🔄 Fallback final: Navegando de vuelta a la URL original: {original_url}")
                    
                    try:
                        await page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(3000)
                        
                        # Hacer scraping directo con scroll infinito
                        self.logger.info("📜 Fallback final: Iniciando scraping directo con scroll infinito...")
                        await self.await_products_loaded(page)
                        productos_cargados = await self.scroll_to_load_all_products(page)
                        self.logger.info(f"✅ Fallback final completado: {productos_cargados} productos extraídos")
                        
                        content = await page.content()
                        from scrapy.http import HtmlResponse
                        updated_response = HtmlResponse(
                            url=original_url,
                            body=content,
                            encoding='utf-8'
                        )
                        # Extraer categoría de la URL para usar como subcategoría
                        category_name = self.extract_category_from_url(original_url)
                        for item in self.parse_products(updated_response, category_name):
                            yield item
                            
                    except Exception as fallback_error:
                        self.logger.error(f"❌ Error en fallback final: {fallback_error}")
                    
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
            # Extraer categoría de la URL para usar como subcategoría
            category_name = self.extract_category_from_url(str(page.url))
            for item in self.parse_products(updated_response, category_name):
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

    async def parse_products(self, response, category_name="farmacia", subcategory_name=None):
        """
        Extrae productos ÚNICAMENTE después de que el scroll se haya completado y la página esté estable.
        Utiliza el selector correcto: //fp-filtered-product-list//fp-product-large (Card de producto)
        """
        # Obtener el objeto page de Playwright
        page = response.meta.get("playwright_page")
        if not page:
            self.logger.error("❌ No hay página de Playwright disponible")
            return
        
        # Realizar scroll completo para cargar todos los productos
        await self.scroll_to_load_all_products(page)
        
        # Actualizar el response con el contenido después del scroll
        updated_content = await page.content()
        response = response.replace(body=updated_content.encode('utf-8'))
        
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
                
                # Asignar categoría y subcategoría según especificación
                # Siempre usar "farmacia" como categoría principal
                item['category'] = category_name if category_name else "farmacia"
                item['sub_category'] = subcategory_name if subcategory_name else None
                
                # Información comercial
                item['comercial_name'] = inkafarma.COMERCIAL_NAME
                item['comercial_id'] = inkafarma.COMERCIAL_ID
                
                yield item
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando producto {i+1}: {e}")
                continue
        
        self.logger.info(f"✅ Scraping completado: {len(productos)} productos extraídos{context} (después del scroll completo)")
    
    def extract_category_from_subcategory(self, subcategory_name):
        """
        Extrae la categoría principal de una subcategoría usando la estructura JSON cuando esté disponible
        """
        try:
            # Priorizar búsqueda en la estructura JSON
            if self.structure_data and isinstance(self.structure_data.get('categories'), dict):
                for categoria_key, categoria_obj in self.structure_data['categories'].items():
                    subcats = categoria_obj.get('subcategories', {}) or {}
                    # Buscar por slug (clave) o por nombre visible
                    if subcategory_name in subcats:
                        return categoria_key
                    for subkey, subobj in subcats.items():
                        name = subobj.get('name', '')
                        if name and subcategory_name.lower() == name.lower():
                            return categoria_key

            # Si no se encuentra en JSON, intentar heurísticas sobre el texto
            if 'packs' in subcategory_name.lower():
                return 'inka-packs'
            elif 'bebe' in subcategory_name.lower() or 'mama' in subcategory_name.lower():
                return 'mama-y-bebe'
            elif 'dermocosmetica' in subcategory_name.lower() or 'dermocosmetica' in subcategory_name.lower():
                return 'dermatologia-cosmetica'
            elif 'suplementos' in subcategory_name.lower():
                return 'nutricion-para-todos'
            else:
                return 'farmacia'  # Categoría por defecto (en minúscula, consistente con uso JSON)

        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo extraer categoría de '{subcategory_name}': {e}")
            return 'farmacia'
    
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
    
    def extract_category_raw_from_url(self, url):
        """Extrae la categoría desde la URL en formato raw (sin conversión) para buscar en diccionarios"""
        try:
            # URL format: https://inkafarma.pe/categoria/categoria-nombre?params
            if '/categoria/' in url:
                # Obtener parte después de /categoria/
                categoria_part = url.split('/categoria/')[-1]
                # Limpiar parámetros de query (?param=value)
                categoria = categoria_part.split('?')[0]
                # Limpiar fragmentos (#fragment)
                categoria = categoria.split('#')[0]
                return categoria.strip()
            return "general"
        except Exception:
            return "general"