import re
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scraper.spiders.constants import jumbo
from scrapy.http import Response
from playwright.async_api import Page
import time


class JumboSpider(scrapy.Spider):
    name = "jumbo"
    
    allowed_domains = ["www.jumbocolombia.com"]
    
    def __init__(self, name = None, **kwargs):
        super().__init__(name, **kwargs)
        category = self.category if hasattr(self, 'category') else None
        part = self.part if hasattr(self, 'part') else None
        self.start_urls = []
        if category and part: 
            if category in 'supermarket' and part == '1':
                self.start_urls = jumbo.START_URLS_SUPERMARKET_1
            elif category in 'supermarket' and part == '2':
                self.start_urls = jumbo.START_URLS_SUPERMARKET_2
            elif category in 'electronic':
                self.start_urls = jumbo.START_URLS_ELECTRO
        else:
            self.start_urls = jumbo.START_URLS_SUPERMARKET_1 + jumbo.START_URLS_SUPERMARKET_2 + jumbo.START_URLS_ELECTRO
    
    async def start(self):
        self.logger.info("Lanzando navegador Playwright...")
        for url in self.start_urls:
            self.logger.info(f"Iniciando scraping para la categoría principal: {url}")
            yield scrapy.Request(
                url,
                meta=dict(playwright=True, playwright_include_page=True,
                          playwright_page_methods=[
                              PageMethod(
                                  "wait_for_selector", jumbo.SELECTOR_LOAD_PRODUCTS,timeout=90000),
                          ],
                          playwright_page_goto_kwargs={
                              "wait_until": "domcontentloaded",
                              "timeout": 60000
                          }
                          ),

                callback=self.orchestrator,
                errback=self.errback_close_page
            )
        print("Todas las solicitudes iniciales han sido enviadas.")
        
    async def handle_age_verification(self, page: Page):
        try:
            await page.wait_for_selector(jumbo.SELECTOR_OLDER_AGE, timeout=10000)
            original_url = page.url
            print("Página de verificación de edad detectada. Intentando hacer clic en el botón...")
            older_age_button = page.locator(jumbo.SELECTOR_OLDER_AGE)
            if await older_age_button.count() > 0:
                await older_age_button.first.click()
                print("Clic en el botón de verificación de edad realizado.")
                await page.wait_for_timeout(2000)  # Espera para asegurarse de que la página se actualice
                await page.goto(original_url, wait_until="domcontentloaded", timeout=60000)
            else:
                print("No se encontró el botón de verificación de edad.")
        except Exception as e:
            print(f"No se detectó una página de verificación de edad. Continuando con el scraping. Error: {e}")
    
    async def orchestrator(self, response: Response):
        """
        Esta función actúa como un director de orquesta.
        Primero, determina si la página actual tiene demasiados productos.
        """
        page: Page = response.meta["playwright_page"]
        
        try:
            if ("cigarrillos-y-tabacos" in response.url):
                await page.wait_for_timeout(2000) 
                await self.handle_age_verification(page)
            total_products_element = await page.wait_for_selector(jumbo.SELECTOR_TOTAL_COUNT_PRODUCTS, timeout=15000)
            total_products_text = await total_products_element.inner_text()
            total_products = int(re.sub(r'[^\d]', '', total_products_text))
        except Exception as e:
            self.logger.warning(f"No se pudo determinar el total de productos para {response.url}. Procediendo con scrapeo directo. Error: {e}")
            await page.wait_for_timeout(2000)
            total_products = 0 
        try:
            print(f"Total de productos en {response.url}: {total_products}")
            if total_products > 1400:
                self.logger.info(f"La categoría {response.url} tiene {total_products} productos. Se requiere descubrir subcategorías.")
                async for request in self.discover_subcategories(response):
                    yield request
            else: 
                self.logger.info(f"La categoría {response.url} tiene {total_products} productos. Scrapeando directamente.")
                async for item in self.parse_category(response):
                    yield item
        except Exception as e:
            self.logger.error(f"Error durante la orquestación para {response.url}: {e}")
            await page.close()
    
    async def parse_category(self, response: Response):
        page: Page = response.meta["playwright_page"]
        page_number = 1
        try:
            while True:
                try:
                    async for item in self.save_products_count(page, page_number, response):
                        yield item
                    await page.wait_for_timeout(2000)
                    next_page_button = page.locator(
                        f"xpath={jumbo.XPATH_CLICK_BUTTON}")

                    if await next_page_button.count() > 0:
                        print("Botón 'Siguiente' encontrado. Navegando a la siguiente página...")
                        await page.wait_for_timeout(2000) 
                        await next_page_button.first.click()
                        print("Clic en el botón 'Siguiente' realizado.")
                        await page.wait_for_timeout(2000) 
                        await page.wait_for_selector(jumbo.SELECTOR_LOAD_PRODUCTS, timeout=90000)
                        page_number += 1
                    else:
                        print("No se encontró el botón 'Siguiente'. Fin de la categoría.")
                        break
                except Exception as e:
                    self.logger.error(f"Error al procesar la página {page_number} de {response.url}: {e}")
                    break
        except Exception as e:
            self.logger.error(f"Error al parsear la categoría {response.url} en la página {page_number}: {e}")
        finally:
            await page.close()
            print(f"Cerrada la página para {response.url}")
  
    async def discover_subcategories(self, response:Response):
        page:Page = response.meta["playwright_page"]
        try:
            self.logger.info("Etapa 1: Descubriendo subcategorías...")
            await page.click(jumbo.XPATH_BUTTON_GET_CATEGORIES)
            await page.wait_for_timeout(2000) 
            pages = page.url.split("/")
            selector_get_category = f"a[href='/{pages[-2].strip()}'][class*='jumbo-main-menu-2-x-link--header-submenu-item']"
            
            category_element = await page.wait_for_selector(selector_get_category, timeout=60000)
            self.logger.info(f"Haciendo hover sobre: {pages[-2].strip()}")
            await category_element.hover()
            
            await page.wait_for_timeout(3000)
            get_sub_category = f"{jumbo.XPATH_CATEGORY_SUB_CATEGORY}/div/span/a[contains(@href,'/{pages[-1].strip()}')]/../..//a[contains(@class, 'item_node_inner_third_level--header-submenu-item')]"
            links = await page.locator(get_sub_category).all()
            subcategory_urls = set()
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = response.urljoin(href)
                    subcategory_urls.add(full_url)
            
                self.logger.info(f"Se encontraron {len(subcategory_urls)} URLs de subcategorías.")
        except Exception as e:
            self.logger.error(f"Error al descubrir subcategorías en {response.url}: {e}")
        finally:
            await page.close()

        # Etapa 2: Por cada URL encontrada, lanzamos el scraper de productos
        for url in subcategory_urls:
            self.logger.info(f"Iniciando scraping para la subcategoría: {url}")
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded", "timeout": 60000
                    }
                },
                callback=self.parse_category,
                errback=self.errback_close_page
            )

    
    
    async def save_products_count(self, page, page_number, response ):
        print(f"Scrapeando página {page_number} de '{response.url}'...")
        await self.await_products_loaded(page)
        html_content = await page.content()
        scrapy_selector = scrapy.Selector(text=html_content)
        breadcrumbs = scrapy_selector.xpath(
            jumbo.XPATH_GET_BREADCRUMBS).getall()
        category = breadcrumbs[0]
        sub_category = breadcrumbs[1]
        for product_card in scrapy_selector.xpath(jumbo.XPATH_GET_ALL_PRODUCTS):
            yield self.take_products_fields(product_card, category, sub_category)

    
    def take_products_fields(self, product_card: scrapy.Selector, category, sub_category):

        item = ScraperItem()

        name = product_card.xpath('.//h3/span//text()').get().strip()
        item['name'] = name
        matches = re.findall(
            r'(\d+[\.,]?\d*)\s?((?:g|gr|ml|l|lt|kg|onz|lb|unidades|unideades|un|cm|m|u|grs|und|unds|g[a-z]*)\b)', name, re.IGNORECASE)
        if matches:
            value = matches[-1]
            item['total_unit_quantity'] = float(value[0].replace(',', '.'))
            item['unit_type'] = value[1]
        else:
            matches = re.findall(jumbo.REGULAR_EXPRESSION_UNITS_SIMPLE, name.lower(), re.IGNORECASE)
            if matches:
                value = matches[-1]
                item['total_unit_quantity'] = float(value.replace('.', '').replace(',', '.')) if type(value) == str else float(value[0].replace('.', '').replace(',', '.'))
                item['unit_type'] = 'un'
            else:
                item["total_unit_quantity"] = 1
                item['unit_type'] = 'un'
        item['category'] = category
        item['sub_category'] = sub_category
        item['comercial_name'] = jumbo.NAME

        item['comercial_id'] = jumbo.ID

        price_text = product_card.xpath(jumbo.XPATH_GET_PRICE).getall()[-1]
        item['price'] = float(price_text.strip().replace(
            '$', '').replace('.', '').replace(",", ".").strip())

        unit_price_text = product_card.xpath(
            jumbo.XPATH_UNIT_PRICE).get()
        if unit_price_text:
            # 1. Busca el patrón de número (puede tener comas o puntos) en el texto
            price_match = re.search(r'(\d+[\.,]\d*)', unit_price_text.strip())
            if price_match:
                item['unit_price'] = float(
                    price_match.group(1).replace(',', '.'))
            else:
                item['unit_price'] = float(
                    item.get("price")) / float(item["total_unit_quantity"])
        else:
            item['unit_price'] = float(
                item.get("price")) / float(item["total_unit_quantity"])

        return item

    async def await_products_loaded(self, page: Page):
        await page.wait_for_timeout(2000)  # Espera inicial para asegurarse de que la página esté completamente cargada
        await page.wait_for_selector(jumbo.SELECTOR_LOAD_PRODUCTS, timeout=60000)
        previous_height = -1
        while True:
            try:
                await page.wait_for_selector(jumbo.SELECTOR_CONTAINER_PRODUCTS, timeout=60000)
            except Exception:
                self.logger.warning("El contenedor de productos no apareció. Saltando el scroll.")
                break
            current_height = await page.evaluate(f"document.querySelector('{jumbo.SELECTOR_CONTAINER_PRODUCTS}').scrollHeight")

            if current_height == previous_height:
                print(
                    "La altura del contenedor se ha estabilizado. Scroll finalizado para esta página.")
                break

            try:
                previous_height = current_height
                print("Haciendo scroll hasta el final...")
                await page.evaluate(f"window.scrollTo(0, {current_height})")
                # Espera crucial para dar tiempo a que se carguen y rendericen los nuevos productos
                await page.wait_for_timeout(3000)  # Ajusta este tiempo según sea necesario
            except Exception as e:
                self.logger.error(f"Error durante el scroll: {e}")
                break

    async def errback_close_page(self, failure):
        # Callback de error robusto para cerrar la página si algo falla
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Ocurrió un error al procesar {failure.request.url}: {failure.value}")
