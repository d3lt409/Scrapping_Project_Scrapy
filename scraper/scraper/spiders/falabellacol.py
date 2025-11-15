import re
import playwright
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scraper.spiders.constants import falabellacol
from scrapy.http import Response
from playwright.async_api import Page, Locator


class FalabellacolSpider(scrapy.Spider):
    name = "falabellacol"
    pais = "colombia"
    allowed_domains = ["www.falabella.com.co"]
    start_urls = ["https://www.falabella.com.co/falabella-co"]

    async def start(self):
        self.logger.info("Lanzando navegador Playwright...")
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(playwright=True, playwright_include_page=True,

                          playwright_page_goto_kwargs={
                              "wait_until": "domcontentloaded",
                              "timeout": 60000
                          }
                          ),

                callback=self.orchestrate_requests,
                errback=self.handle_error
            )

    async def orchestrate_requests(self, response: Response):
        page: Page = response.meta["playwright_page"]
        categories_urls = await self._get_categories(page)
        await page.close()
        self.logger.info(
            "Categorías y subcategorías obtenidas, comenzando solicitudes...")
        for category, subcategories in categories_urls.items():
            for subcategory, urls in subcategories.items():
                for url in urls:
                    yield scrapy.Request(
                        url,
                        meta=dict(playwright=True, playwright_include_page=True,
                                  playwright_page_methods=[
                                      PageMethod(
                                          "wait_for_selector", falabellacol.SELECTOR_LOAD_PRODUCTS, timeout=90000),
                                  ],
                                  playwright_page_goto_kwargs={
                                      "wait_until": "domcontentloaded",
                                      "timeout": 60000
                                  }
                                  ),
                        cb_kwargs={
                            "category": category,
                            "sub_category": subcategory
                        },
                        callback=self.parse,
                        errback=self.handle_error
                    )
        self.logger.info("Todas las solicitudes generadas.")

    async def _get_categories(self, page: Page):
        await page.wait_for_timeout(3000)
        button_categories = await page.wait_for_selector(
            falabellacol.SELECTOR_BUTTON_CATEGORIES)
        await page.wait_for_timeout(2000)
        if button_categories:
            await button_categories.click()

        self.logger.info("Obteniendo categorías y subcategorías...")
        await page.wait_for_timeout(2000)
        categories_urls = {}
        if hasattr(self, "category") and self.category:
            categories_elements = page.locator(falabellacol.XPATH_CATEGORY_NAME.replace(
                "{category}", self.category))
            if await categories_elements.count() > 0:
                element = categories_elements.first
                category_name = await element.inner_text()
                category_name = category_name.strip()
                categories_urls[category_name] = {}
                await element.hover()
                await page.wait_for_timeout(2000)

                await self._get_sub_categories(page, category_name, categories_urls)

        else:
            categories_elements = await page.locator(
                falabellacol.XPATH_CATEGORIES).all()

            self.logger.info(
                "Categorías encontradas, procesando subcategorías...")

            for element in categories_elements:
                category_name = await element.inner_text()
                category_name = category_name.strip()

                if category_name in falabellacol.LIST_CATEGORIES:
                    # Inicializamos el diccionario para esta categoría
                    categories_urls[category_name] = {}
                    await element.hover()
                    await page.wait_for_timeout(2000)

                    self.logger.info(
                        f"Procesando subcategorías para la categoría '{category_name}'...")

                    await self._get_sub_categories(page, category_name, categories_urls)

        return categories_urls

    async def _get_sub_categories(self, page: Page, category_name: str, categories_urls: dict):
        self.logger.info(
            f"Procesando subcategorías para la categoría '{category_name}'...")

        # Obtenemos todas las subcategorías para esta categoría específica
        sub_categories_elements = await page.query_selector_all(
            falabellacol.SELECTOR_SUB_CATEGORIES)

        for sub_element in sub_categories_elements:
            # Obtenemos el nombre de la subcategoría dentro del elemento actual
            sub_category_name = await sub_element.query_selector(falabellacol.SELECTOR_SUB_CATEGORY_NAME)
            if sub_category_name:
                sub_category_name_text = await sub_category_name.inner_text()
                sub_category_name_text = sub_category_name_text.strip()

                # Obtenemos los enlaces para esta subcategoría
                links = await sub_element.query_selector_all(
                    falabellacol.SELECTOR_SUB_CATEGORIES_LINKS)
                url_links = []

                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        url_links.append(href)

                # Solo agregamos la subcategoría si tiene enlaces
                if url_links:
                    categories_urls[category_name][sub_category_name_text] = url_links

    async def parse(self, response: Response, category, sub_category):
        page: Page = response.meta["playwright_page"]

        self.logger.info(
            f"Extrayendo productos de la categoría '{category}' y subcategoría '{sub_category}' en {response.url}")
        while True:
            await self._await_products_loaded(page)
            await page.wait_for_load_state("domcontentloaded")
            try:
                await page.wait_for_timeout(2000)
                await page.wait_for_selector(falabellacol.SELECTOR_PRODUCT_CARDS)
                await page.wait_for_timeout(2000)
            except TimeoutError as e:
                self.logger.warning("No se encontraron productos")
                break

            try:
                await page.wait_for_selector(falabellacol.SELECTOR_PRODUCT_NAME, timeout=60000)
                await page.wait_for_timeout(2000)
                html_content = await page.content()
                scrapy_selector = scrapy.Selector(text=html_content)

                products = scrapy_selector.xpath(
                    falabellacol.XPATH_PRODUCT_CARDS)
                for product_card in products:
                    try:
                        item = self.take_products_fields(
                            product_card, category, sub_category)
                    except Exception as e:
                        self.logger.error(
                            f"Saltando este producto. Error: {e} \n Produc card: {product_card}")
                        continue

                    item['comercial_name'] = falabellacol.NAME
                    item['comercial_id'] = falabellacol.ID
                    yield item

            except Exception as e:
                self.logger.error(
                    f"Error encontrado para esta categoría {category} y sub {sub_category}:\n Error {e}")
            await page.wait_for_timeout(2000)
            try:
                next_page_button: Locator = page.locator(
                    falabellacol.XPATH_NEXT_PAGE_BUTTON)
                if await next_page_button.count() > 0:
                    await next_page_button.first.click()
                    self.logger.info(
                        "Cargando más productos haciendo clic en el botón 'Cargar más'...")
                    # Esperar a que se carguen los nuevos productos
                    await page.wait_for_timeout(2000)
                else:
                    self.logger.info(
                        "No hay más productos para cargar en esta subcategoría.")
                    break
            except playwright._impl._errors.TimeoutError as e:
                self.logger.error(f"Boton no encontrado, fin de la categoría")
                break
        await page.close()
        self.logger.info(
            f"Finalizada la extracción de productos para la categoría {category} y la subcategoría '{sub_category}'.")

    def _get_price(self, product_card):
        price = product_card.xpath(falabellacol.XPATH_PRODUCT_PRICE)

        if price:
            price = price.get().strip().split("-")[-1].strip()
            return float(price.replace(
                '$', '').replace('.', '').strip())

        price = product_card.xpath(falabellacol.XPATH_PRODUCT_PRICE1)
        if (price):
            price = price.get().strip().split("-")[-1].strip()
            return float(price.replace(
                '$', '').replace('.', '').strip())
        price = product_card.xpath(falabellacol.XPATH_PTODUCT_PRICE2)
        if (price):
            price = price.get().strip().split("-")[-1].strip()
            return float(price.replace(
                '$', '').replace('.', '').strip())
        else:
            raise ValueError("Price product not found")

    def take_products_fields(self, product_card: scrapy.Selector, category, sub_category):
        item = ScraperItem()
        price = self._get_price(product_card)
        if price:
            item['price'] = price
        try:
            name = product_card.xpath(
                falabellacol.XPATH_PRODUCT_NAME).get().strip()
        except Exception as e:
            raise ValueError(
                f"Nombre de producto no encontrado ")
        item['name'] = name
        matches = re.findall(
            r'(\d+[\.,]?\d*)\s?((?:g|gr|ml|l|lt|kg|onz|lb|unidades|unideades|un|cm|m|u|grs|und|unds)\b)', name, re.IGNORECASE)
        if len(matches) > 0:
            value = matches[-1]
            item['total_unit_quantity'] = float(value[0].replace(',', '.'))
            item['unit_type'] = value[1].lower()
        else:
            item['total_unit_quantity'] = 1
            item['unit_type'] = 'un'

        item['unit_price'] = float(item['price'] / item['total_unit_quantity'])

        item['category'] = category
        item['sub_category'] = sub_category

        return item

    async def _await_products_loaded(self, page: Page):
        # Espera inicial para asegurarse de que la página esté completamente cargada
        previous_height = -1
        while True:
            try:
                await page.wait_for_selector(falabellacol.SELECTOR_CONTAINER_PRODUCTS, timeout=60000)
            except Exception:
                self.logger.warning(
                    "El contenedor de productos no apareció. Saltando el scroll.")
                break
            current_height = await page.evaluate(f"document.querySelector('{falabellacol.SELECTOR_CONTAINER_PRODUCTS}').scrollHeight")

            if current_height == previous_height:
                self.logger.info(
                    "La altura del contenedor se ha estabilizado. Scroll finalizado para esta página.")
                await page.wait_for_timeout(3000)
                break

            try:
                previous_height = current_height
                self.logger.info("Haciendo scroll hasta el final...")
                await page.evaluate(f"window.scrollTo(0, {current_height})")
                await page.wait_for_timeout(3000)
            except Exception as e:
                self.logger.error(f"Error durante el scroll: {e}")
                break

    async def handle_error(self, failure):
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
            self.logger.warning(
                f"Timeout en Request #{category_index}: {categoria} > {subcategoria}")
            self.logger.warning(f"URL afectada: {original_url}")

            # Intentar un reintento con timeout más largo
            retry_count = request.meta.get('retry_count', 0)
            if retry_count < 2:  # Máximo 2 reintentos
                self.logger.info(
                    f"Reintentando Request #{category_index} (intento {retry_count + 1})")
                retry_request = request.replace(
                    meta={
                        **request.meta,
                        'retry_count': retry_count + 1,
                        'playwright_page_goto_kwargs': {
                            "wait_until": "domcontentloaded",
                            "timeout": 45000  # Timeout más largo para reintentos
                        }
                    }
                )
                return retry_request
            else:
                self.logger.error(
                    f"Máximo de reintentos alcanzado para Request #{category_index}: {categoria} > {subcategoria}")
        else:
            page: Page = failure.request.meta.get("playwright_page")
            if page:
                await page.close()
            self.logger.error(
                f"Ocurrió un error al procesar {failure.request.url}: {failure.value}")
