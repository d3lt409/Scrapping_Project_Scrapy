import scrapy
import re
import asyncio
from scrapy import Request
from scrapy.selector import Selector
from ..items import JuriscolItem
from .constants.juriscol import *


class JuriscolSpider(scrapy.Spider):
    name = "juriscol"
    allowed_domains = ["www.suin-juriscol.gov.co"]
    start_urls = [START_URL]

    def __init__(self, tipos=None, sectores=None, vigencias=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # tipos: comma-separated values like 'Decretos,Leyes,Resolucion'
        self.tipos = tipos.split(',') if tipos else list(TIPOS_NORMA.values())
        # sectores: comma-separated visible labels; if not provided use only prioritarios
        self.sectores = sectores.split(',') if sectores else SECTORES_PRIORITARIOS
        # vigencias: comma-separated values; if not provided use only vigentes
        self.vigencias = vigencias.split(',') if vigencias else ['Vigente', 'Vigente Parcial']
        
        # Contadores para seguimiento
        self.total_extracted = 0
        self.errors_count = 0
        self.combinations_processed = 0
        
    def start_requests(self):
        # Una sola request inicial para procesar todas las combinaciones secuencialmente
        yield Request(
            self.start_urls[0],
            meta={"playwright": True, "playwright_include_page": True},
            callback=self.parse
        )

    async def parse(self, response):
        """Procesa todas las combinaciones tipo+sector secuencialmente con manejo robusto de errores"""
        page = response.meta.get("playwright_page")
        if not page:
            self.logger.error("No se obtuvo la página de Playwright")
            return

        try:
            # Configurar página para mejor rendimiento
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.set_extra_http_headers({"Accept-Language": "es-ES,es;q=0.9"})
            
            self.logger.info(f"Iniciando scraping secuencial de {len(self.tipos)} tipos x {len(self.sectores)} sectores x {len(self.vigencias)} vigencias = {len(self.tipos) * len(self.sectores) * len(self.vigencias)} combinaciones")
            
            for tipo_index, tipo in enumerate(self.tipos):
                # Navegar a URL principal al cambiar de tipo de norma (excepto en el primero)
                if tipo_index > 0:
                    self.logger.info(f"Cambiando a tipo de norma: {tipo} - Navegando a URL principal")
                    await page.goto(START_URL, wait_until="networkidle")
                    await asyncio.sleep(1)
                for sector_index, sector in enumerate(self.sectores):
                    for vigencia_index, vigencia in enumerate(self.vigencias):
                        # Navegar a URL principal al cambiar de vigencia para resetear el formulario
                        if vigencia_index > 0:
                            self.logger.info(f"Cambiando a vigencia: {vigencia} - Navegando a URL principal")
                            await page.goto(START_URL, wait_until="networkidle")
                            await asyncio.sleep(1)
                        
                        self.combinations_processed += 1
                        self.logger.info(f"[{self.combinations_processed}/{len(self.tipos) * len(self.sectores) * len(self.vigencias)}] Procesando {tipo} / {sector} / {vigencia}")
                        async for item in self.process_combination_with_retries(page, tipo, sector, vigencia, max_retries=3):
                            yield item
                        await asyncio.sleep(0.5)
            self.logger.info(f"Scraping completado: {self.total_extracted} items extraídos con {self.errors_count} errores.")
        except Exception as e:
            self.logger.error(f"Error general en parse: {e}")
        finally:
            try:
                await page.close()
            except Exception as e:
                self.logger.error(f"Error cerrando la página: {e}")

    async def process_combination_with_retries(self, page, tipo, sector, vigencia, max_retries=3):
        """Procesa una combinación con sistema de reintentos robusto"""
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Reintento {attempt}/{max_retries} para {tipo}/{sector}/{vigencia}")
                    await asyncio.sleep(2 ** (attempt - 1))
                
                # Navegar a URL principal si es un reintento
                if attempt > 0:
                    self.logger.info(f"Navegando a URL principal para reintentar {tipo}/{sector}/{vigencia} (intento {attempt})")
                    await page.goto(START_URL, wait_until="networkidle")
                    await asyncio.sleep(1)
                
                # Procesar combinación y hacer yield de items
                item_count = 0
                async for item in self.process_single_combination(page, tipo, sector, vigencia):
                    yield item
                    item_count += 1
                    self.total_extracted += 1
                
                self.logger.info(f"✓ {tipo}/{sector}/{vigencia}: {item_count} items extraídos")
                return  # Éxito
                    
            except Exception as e:
                self.logger.warning(f"Intento {attempt + 1} falló para {tipo}/{sector}/{vigencia}: {e}")
                if attempt < max_retries:
                    continue
                else:
                    self.logger.error(f"Todos los intentos fallaron para {tipo}/{sector}/{vigencia}")
                    self.errors_count += 1
                    return

    async def process_single_combination(self, page, tipo, sector, vigencia):
        """Procesa una sola combinación tipo+sector+vigencia con manejo de errores detallado"""
        try:
            # 1. Desplegar formulario con reintentos
            form_deployed = await self.deploy_form_with_retries(page)
            if not form_deployed:
                raise Exception("No se pudo desplegar el formulario")
            
            # 2. Seleccionar tipo de norma
            await self.select_tipo_norma(page, tipo)
            
            # 3. Seleccionar sector
            sector_selected = await self.select_sector(page, sector)
            if not sector_selected:
                raise Exception(f"No se pudo seleccionar el sector: {sector}")
            
            # 4. Seleccionar estado de vigencia
            vigencia_selected = await self.select_vigencia(page, vigencia)
            if not vigencia_selected:
                raise Exception(f"No se pudo seleccionar la vigencia: {vigencia}")
            
            # 5. Enviar formulario
            form_submitted = await self.submit_form(page)
            if not form_submitted:
                raise Exception("No se pudo enviar el formulario")
            
            # 6. Extraer datos con paginación (retorna directamente los items)
            async for item in self.extract_all_pages(page, tipo, sector, vigencia):
                yield item
            
        except Exception as e:
            self.logger.error(f"Error en process_single_combination {tipo}/{sector}/{vigencia}: {e}")
            raise  # Re-lanzar la excepción para que sea manejada por el sistema de reintentos

    async def deploy_form_with_retries(self, page, max_attempts=3):
        """Despliega el formulario con múltiples intentos"""
        for attempt in range(max_attempts):
            try:
                # Esperar a que la página esté lista
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                # Esperar que el botón esté disponible
                await page.wait_for_selector(SELECTORS['TOGGLE_FORM_BUTTON'], timeout=5000)
                
                # Verificar si el formulario ya está desplegado
                form_visible = await page.is_visible('select[name="tipo"]')
                if form_visible:
                    self.logger.debug(f"Formulario ya está visible en intento {attempt + 1}")
                    return True
                
                # Si no está visible, hacer clic en el botón para desplegarlo
                await page.click(SELECTORS['TOGGLE_FORM_BUTTON'])
                
                # Esperar a que aparezca el selector de tipo
                await page.wait_for_selector('select[name="tipo"]', timeout=3000)
                await asyncio.sleep(0.5)
                
                # Verificar que realmente esté visible
                if await page.is_visible('select[name="tipo"]'):
                    self.logger.debug(f"Formulario desplegado exitosamente en intento {attempt + 1}")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Intento {attempt + 1} de desplegar formulario falló: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)
                    continue
        
        return False

    async def select_tipo_norma(self, page, tipo):
        """Selecciona el tipo de norma con validación"""
        await page.wait_for_selector(SELECTORS['TIPO_NORMA_SELECT'], timeout=1000)
        await page.select_option(SELECTORS['TIPO_NORMA_SELECT'], value=tipo)
        
        # Disparar eventos para activar validaciones JavaScript
        await page.evaluate("""
            const select = document.querySelector('select[name=\"tipo\"]');
            if (select) {
                select.dispatchEvent(new Event('change', { bubbles: true }));
                select.dispatchEvent(new Event('input', { bubbles: true }));
            }
        """)
        await asyncio.sleep(0.5)  # Dar tiempo para que se procesen los eventos

    async def select_sector(self, page, sector):
        """Selecciona el sector con JavaScript robusto"""
        js_select_sector = f"""
        (function() {{
            const sectorSelect = document.querySelector('select[name="sector"]');
            if (!sectorSelect) return {{ success: false, error: 'select-not-found' }};
            
            const options = Array.from(sectorSelect.options);
            const targetOption = options.find(option => 
                option.text.trim() === '{sector}' || 
                option.value === '{sector}' ||
                option.text.trim().toLowerCase() === '{sector.lower()}'
            );
            
            if (!targetOption) {{
                return {{ 
                    success: false, 
                    error: 'option-not-found', 
                    available: options.slice(0, 5).map(o => o.text.trim()) 
                }};
            }}
            
            sectorSelect.value = targetOption.value;
            sectorSelect.selectedIndex = targetOption.index;
            
            // Disparar eventos
            sectorSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
            sectorSelect.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            return {{ success: true, value: targetOption.value, text: targetOption.text }};
        }})();
        """
        
        result = await page.evaluate(js_select_sector)
        if result and result.get('success'):
            await asyncio.sleep(0.2)
            return True
        else:
            self.logger.error(f"Error seleccionando sector {sector}: {result}")
            return False

    async def select_vigencia(self, page, vigencia):
        """Selecciona el estado de vigencia con JavaScript robusto"""
        js_select_vigencia = f"""
        (function() {{
            const vigenciaSelect = document.querySelector('select[name="estado_documento"]');
            if (!vigenciaSelect) return {{ success: false, error: 'select-not-found' }};
            
            const options = Array.from(vigenciaSelect.options);
            const targetOption = options.find(option => 
                option.text.trim() === '{vigencia}' || 
                option.value === '{vigencia}' ||
                option.text.trim().toLowerCase() === '{vigencia.lower()}'
            );
            
            if (!targetOption) {{
                return {{ 
                    success: false, 
                    error: 'option-not-found', 
                    available: options.slice(0, 5).map(o => o.text.trim()) 
                }};
            }}
            
            vigenciaSelect.value = targetOption.value;
            vigenciaSelect.selectedIndex = targetOption.index;
            
            // Disparar eventos
            vigenciaSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
            vigenciaSelect.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            return {{ success: true, value: targetOption.value, text: targetOption.text }};
        }})();
        """
        
        result = await page.evaluate(js_select_vigencia)
        if result and result.get('success'):
            await asyncio.sleep(0.3)
            return True
        else:
            self.logger.error(f"Error seleccionando vigencia {vigencia}: {result}")
            return False

    async def submit_form(self, page):
        """Envía el formulario con múltiples métodos de respaldo"""
        # Lista de selectores de botones de búsqueda en orden de prioridad
        button_selectors = [
            SELECTORS.get('BUSCAR_BUTTON'),
            SELECTORS.get('BUSCAR_BUTTON_ALT'), 
            SELECTORS.get('BUSCAR_BUTTON_ALT2'),
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Buscar")',
            'input[value*="Buscar"]'
        ]
        
        # Intentar con cada selector
        for selector in button_selectors:
            if not selector:
                continue
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    await self.wait_for_results(page)
                    return True
            except Exception:
                continue
        
        # Método de respaldo: envío directo del formulario
        try:
            await page.evaluate("document.querySelector('#mainForm')?.submit()")
            await self.wait_for_results(page)
            return True
        except Exception as e:
            self.logger.error(f"Error en envío de formulario: {e}")
            return False

    async def wait_for_results(self, page):
        """Espera a que aparezcan los resultados con manejo de errores"""
        try:
            await page.wait_for_selector(
                f"{SELECTORS['RESULTS_TABLE']}, .no-results, .sin-resultados",
                timeout=4000
            )
            await asyncio.sleep(1)  # Estabilización
        except Exception as e:
            self.logger.warning(f"Timeout esperando resultados: {e}")
            raise

    async def extract_all_pages(self, page, tipo, sector, vigencia):
        """Extrae todos los datos con paginación optimizada y manejo de errores"""
        extracted_count = 0
        page_number = 1
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        # Intentar obtener el total esperado de la paginación
        total_expected = await self.get_total_expected(page)
        if total_expected:
            self.logger.info(f"Total esperado para {tipo}/{sector}/{vigencia}: {total_expected}")
        
        while True:
            try:
                # Verificar que estamos en una página válida
                if not await self.is_valid_results_page(page):
                    self.logger.warning(f"Página {page_number} no válida para {tipo}/{sector}/{vigencia}")
                    break
                
                # Extraer datos de la página actual
                page_items = await self.extract_page_items(page, tipo, sector, vigencia)
                
                if not page_items:
                    self.logger.info(f"No hay más items en página {page_number} para {tipo}/{sector}/{vigencia}")
                    break
                
                # Procesar items de esta página
                for item in page_items:
                    yield item
                    extracted_count += 1
                
                self.logger.info(f"Página {page_number}: {len(page_items)} items extraídos ({extracted_count} total)")
                
                # Verificar si ya tenemos todos los items esperados
                if total_expected and extracted_count >= total_expected:
                    self.logger.info(f"Alcanzado total esperado ({total_expected}) para {tipo}/{sector}/{vigencia}")
                    break
                
                # Intentar ir a la siguiente página
                has_next = await self.go_to_next_page(page)
                if not has_next:
                    self.logger.info(f"No hay más páginas para {tipo}/{sector}/{vigencia}")
                    break
                
                page_number += 1
                consecutive_errors = 0  # Reset contador de errores
                
                # Pausa entre páginas para estabilidad
                # await asyncio.sleep(0.3)  # Eliminado para mayor velocidad
                
            except Exception as e:
                consecutive_errors += 1
                self.logger.warning(f"Error en página {page_number} para {tipo}/{sector}/{vigencia} (error {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(f"Demasiados errores consecutivos en {tipo}/{sector}/{vigencia}, abortando")
                    break
                
                # Pausa más larga en caso de error
                await asyncio.sleep(1 + consecutive_errors)
                continue

    async def get_total_expected(self, page):
        """Obtiene el total esperado de items desde la información de paginación"""
        try:
            pagination_elem = await page.query_selector(SELECTORS['PAGINATION_INFO'])
            if not pagination_elem:
                return None
            
            pagination_text = await pagination_elem.inner_text()
            if not pagination_text:
                return None
            
            # Buscar patrón: "X a Y de Z"
            match = re.search(r"(\d+)\s+a\s+(\d+)\s+de\s+(\d+)", pagination_text.strip())
            if match:
                return int(match.group(3))
            
            # Buscar patrón alternativo: "Página X de Y (Z elementos)"
            alt_match = re.search(r"\((\d+)\s+elementos?\)", pagination_text.strip())
            if alt_match:
                return int(alt_match.group(1))
                
        except Exception as e:
            self.logger.debug(f"No se pudo obtener total esperado: {e}")
        
        return None

    async def is_valid_results_page(self, page):
        """Verifica si la página actual tiene resultados válidos"""
        try:
            # Verificar que existe la tabla de resultados
            table_exists = await page.query_selector(SELECTORS['RESULTS_TABLE'])
            if not table_exists:
                return False
            
            # Verificar que no hay mensaje de "sin resultados"
            no_results = await page.query_selector('.no-results, .sin-resultados, .empty-results')
            if no_results:
                return False
            
            # Verificar que hay al menos una fila de datos
            rows = await page.query_selector_all(SELECTORS['RESULTS_ROWS'])
            return len(rows) > 0
            
        except Exception:
            return False

    async def extract_page_items(self, page, tipo, sector, vigencia):
        """Extrae todos los items de la página actual"""
        items = []
        
        try:
            # Obtener HTML de la página
            html = await page.content()
            sel = Selector(text=html)
            
            # Extraer todas las filas de resultados
            rows = sel.css(SELECTORS['RESULTS_ROWS'])
            
            for row in rows:
                try:
                    item = JuriscolItem()
                    item['tipo'] = row.css(SELECTORS['COLUMN_TIPO'] + '::text').get(default='').strip()
                    item['numero'] = row.css(SELECTORS['COLUMN_NUMERO'] + '::text').get(default='').strip()
                    item['ano'] = row.css(SELECTORS['COLUMN_ANO'] + '::text').get(default='').strip()
                    item['sector'] = row.css(SELECTORS['COLUMN_SECTOR'] + '::text').get(default='').strip()
                    item['emisor'] = row.css(SELECTORS['COLUMN_EMISOR'] + '::text').get(default='').strip()
                    item['estado'] = row.css(SELECTORS['COLUMN_ESTADO'] + '::text').get(default='').strip()
                    item['epigrafe'] = row.css(SELECTORS['COLUMN_EPIGRAFE'] + '::text').get(default='').strip()
                    
                    # Extraer URL del documento
                    link = row.css(SELECTORS['COLUMN_ACCIONES'] + ' ' + SELECTORS['DOCUMENT_LINK'] + '::attr(href)').get()
                    if link:
                        item['documento_url'] = link if link.startswith('http') else BASE_URL + link
                    else:
                        item['documento_url'] = None
                    
                    # Validar que el item tiene datos mínimos
                    if item['tipo'] or item['numero'] or item['epigrafe']:
                        items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"Error extrayendo item individual: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error extrayendo items de página: {e}")
        
        return items

    async def go_to_next_page(self, page):
        """Navega a la siguiente página con múltiples métodos de detección"""
        try:
            # Método 1: Buscar botón/enlace "Siguiente" o flecha derecha
            next_selectors = [
                'img[src$="arrow-right-icon.png"]',
                'a:has-text("Siguiente")',
                'a:has-text(">")',
                '.pagination .next:not(.disabled)',
                '.pagination a[aria-label="Siguiente"]'
            ]
            
            for selector in next_selectors:
                try:
                    element = await page.query_selector(selector)
                    if not element:
                        continue
                    
                    # Si es una imagen, buscar el enlace padre
                    if 'img' in selector:
                        parent_link = await element.evaluate_handle('node => node.closest("a")')
                        if parent_link:
                            href = await (await parent_link.get_property('href')).json_value()
                            if href and href.strip() and href.strip() != '#':
                                await parent_link.as_element().click()
                                await self.wait_for_results(page)
                                return True
                    else:
                        # Para enlaces directos
                        href = await element.get_attribute('href')
                        if href and href.strip() and href.strip() != '#':
                            await element.click()
                            await self.wait_for_results(page)
                            return True
                            
                except Exception:
                    continue
            
            # Método 2: JavaScript para detectar paginación automáticamente
            next_available = await page.evaluate("""
                () => {
                    // Buscar enlaces que contengan números de página
                    const links = Array.from(document.querySelectorAll('a[href*="page"], a[href*="pag"]'));
                    const currentPage = window.location.href;
                    
                    // Buscar el siguiente número de página
                    for (let link of links) {
                        if (link.href !== currentPage && link.href !== '#') {
                            return { found: true, href: link.href };
                        }
                    }
                    
                    return { found: false };
                }
            """)
            
            if next_available.get('found'):
                await page.goto(next_available['href'], wait_until="networkidle")
                return True
            
        except Exception as e:
            self.logger.debug(f"Error navegando a siguiente página: {e}")
        
        return False