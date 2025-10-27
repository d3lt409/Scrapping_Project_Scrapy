import re
import json
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scrapy.http import Response
from playwright.async_api import Page
import os
 
 
class InkatestSpider(scrapy.Spider):
    name = "inkatest"
    pais = "peru"
    allowed_domains = ["inkafarma.pe"]
    start_urls = ["https://inkafarma.pe/"]
    custom_settings = {
        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 1920, "height": 1080},
            }
        }
    }
 
    def start_requests(self):
        self.logger.info("Lanzando navegador Playwright...")
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(playwright=True, playwright_include_page=True,
                          playwright_page_methods=[
                              PageMethod(
                                  "wait_for_selector", "div[class='category-header-container category-menu-header']", timeout=10000),
                          ],
                          playwright_page_goto_kwargs={
                              "wait_until": "domcontentloaded",
                              "timeout": 60000
                          }
                          ),
 
                callback=self.parse
            )
 
    async def parse(self, response: Response):
        self.logger.info("Iniciando extracción completa de estructura InkaFarma...")
        page: Page = response.meta["playwright_page"]
        
        # Estructura completa que vamos a construir
        inkafarma_structure = {
            "metadata": {
                "extracted_date": "2025-10-22",
                "total_categories": 0,
                "total_subcategories": 0,
                "total_subsubcategories": 0,
                "extraction_notes": "Estructura completa de categorías InkaFarma extraída dinámicamente"
            },
            "categories": {}
        }
        
        await page.wait_for_timeout(3000)
        await page.wait_for_selector("div[class='category-header-container category-menu-header']", timeout=10000)
        await page.hover("div[class='category-header-container category-menu-header']")
        self.logger.info("✅ Hover sobre el menú de categorías realizado.")
        await page.wait_for_timeout(3000)
        
        await page.wait_for_selector("div.department-container > a", timeout=10000)
        categories = await page.query_selector_all("div.department-container > a")
        
        category_count = 0
        subcategory_count = 0
        subsubcategory_count = 0
        
        self.logger.info(f"Encontradas {len(categories)} categorías principales")
        
        for i, category in enumerate(categories, 1):
            try:
                # Extraer información de la categoría principal
                category_name = (await category.inner_text()).strip()
                category_href = await category.get_attribute("href")
                
                if not category_name or not category_href:
                    continue
                    
                # Limpiar el nombre de la categoría para usarlo como clave
                category_key = category_href.replace('/categoria/', '').replace('/', '')
                
                self.logger.info(f" [{i}/{len(categories)}] Procesando categoría: {category_name}")
                
                # Inicializar estructura de la categoría
                inkafarma_structure["categories"][category_key] = {
                    "name": category_name,
                    "href": category_href,
                    "subcategories": {}
                }
                
                category_count += 1
                
                # Hacer hover sobre la categoría
                await category.hover()
                await page.wait_for_timeout(2000)
                
                # Buscar subcategorías
                try:
                    await page.wait_for_selector("div[class*='category-container category-container--width'] > a", timeout=8000)
                    subcategories = await page.query_selector_all("div[class*='category-container category-container--width'] > a")
                    
                    self.logger.info(f"   📂 Encontradas {len(subcategories)} subcategorías")
                    
                    for j, subcategory in enumerate(subcategories, 1):
                        try:
                            # Extraer información de la subcategoría
                            subcategory_name = (await subcategory.inner_text()).strip()
                            subcategory_href = await subcategory.get_attribute("href")
                            
                            if not subcategory_name or not subcategory_href:
                                continue
                                
                            # Limpiar el nombre de la subcategoría para usarlo como clave
                            subcategory_key = subcategory_href.split('/')[-1] if '/' in subcategory_href else subcategory_href
                            
                            self.logger.info(f"      └─ [{j}/{len(subcategories)}] Subcategoría: {subcategory_name}")
                            
                            # Inicializar estructura de la subcategoría
                            inkafarma_structure["categories"][category_key]["subcategories"][subcategory_key] = {
                                "name": subcategory_name,
                                "href": subcategory_href,
                                "subsubcategories": {}
                            }
                            
                            subcategory_count += 1
                            
                            # Hacer hover sobre la subcategoría para buscar sub-subcategorías
                            await subcategory.hover()
                            await page.wait_for_timeout(1500)
                            
                            # Buscar sub-subcategorías
                            try:
                                await page.wait_for_selector("div[class*='subcategory-container subcategory-container--width'] > a", timeout=3000)
                                subsubcategories = await page.query_selector_all("div[class*='subcategory-container subcategory-container--width'] > a")
                                
                                if subsubcategories:
                                    self.logger.info(f"          Encontradas {len(subsubcategories)} sub-subcategorías")
                                    
                                    for k, subsubcategory in enumerate(subsubcategories, 1):
                                        try:
                                            # Extraer información de la sub-subcategoría
                                            subsubcategory_name = (await subsubcategory.inner_text()).strip()
                                            subsubcategory_href = await subsubcategory.get_attribute("href")
                                            
                                            if not subsubcategory_name or not subsubcategory_href:
                                                continue
                                                
                                            # Limpiar el nombre de la sub-subcategoría para usarlo como clave
                                            subsubcategory_key = subsubcategory_href.split('/')[-1] if '/' in subsubcategory_href else subsubcategory_href
                                            
                                            self.logger.info(f"            └─ [{k}/{len(subsubcategories)}] Sub-subcategoría: {subsubcategory_name}")
                                            
                                            # Agregar sub-subcategoría
                                            inkafarma_structure["categories"][category_key]["subcategories"][subcategory_key]["subsubcategories"][subsubcategory_key] = {
                                                "name": subsubcategory_name,
                                                "href": subsubcategory_href
                                            }
                                            
                                            subsubcategory_count += 1
                                            
                                        except Exception as e:
                                            self.logger.warning(f"            ⚠️ Error procesando sub-subcategoría {k}: {e}")
                                            
                            except Exception as e:
                                self.logger.debug(f"         ℹ️ No hay sub-subcategorías para {subcategory_name}")
                                
                        except Exception as e:
                            self.logger.warning(f"      ⚠️ Error procesando subcategoría {j}: {e}")
                            
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Error buscando subcategorías para {category_name}: {e}")
                
                self.logger.info(f"✅ [{i}/{len(categories)}] Completada categoría: {category_name}")
                self.logger.info("─" * 80)
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando categoría {i}: {e}")
        
        # Actualizar metadatos
        inkafarma_structure["metadata"]["total_categories"] = category_count
        inkafarma_structure["metadata"]["total_subcategories"] = subcategory_count
        inkafarma_structure["metadata"]["total_subsubcategories"] = subsubcategory_count
        
        # Guardar estructura en archivo JSON
        json_filename = "inkafarma_complete_structure.json"
        json_path = os.path.join(os.path.dirname(__file__), "constants", json_filename)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(inkafarma_structure, f, ensure_ascii=False, indent=2)
        
        await page.close()
        
        # Log final con resumen
        self.logger.info("EXTRACCIÓN COMPLETADA!")
        self.logger.info("=" * 50)
        self.logger.info(f"📊 RESUMEN DE EXTRACCIÓN:")
        self.logger.info(f"    Categorías principales: {category_count}")
        self.logger.info(f"    Subcategorías: {subcategory_count}")
        self.logger.info(f"    Sub-subcategorías: {subsubcategory_count}")
        self.logger.info(f"    Archivo generado: {json_path}")
        self.logger.info("=" * 50)
        
        return inkafarma_structure