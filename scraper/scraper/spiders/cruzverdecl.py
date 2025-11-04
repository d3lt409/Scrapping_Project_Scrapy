import re
import playwright
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scraper.spiders.constants import cruzverdecl
from scrapy.http import Response
from playwright.async_api import Page, Locator


class CruzverdeclSpider(scrapy.Spider):
    name = "cruzverdecl"
    pais = "chile"
    allowed_domains = ["www.cruzverde.cl"]
    start_urls = ["https://www.cruzverde.cl/"]

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
        await page.wait_for_timeout(3000)
        self.logger.info("Buscando y aceptando botones...")
        try:
            accept_button = await page.wait_for_selector(cruzverdecl.SELECTOR_BUTTON_OFFERS, timeout=30000)
            self.logger.info("Botón de ofertas encontrado, aceptando...")
            await accept_button.click()

        except playwright._impl._errors.TimeoutError:
            self.logger.warning(
                "Botón de ofertas no encontrado, continuando...")
            pass
        await page.wait_for_timeout(2000)
        # Aceptar ubicación si el botón aparece
        try:
            accept_button = await page.wait_for_selector(cruzverdecl.SELECTOR_BUTTON_LOCATION, timeout=30000)
            await accept_button.click()
            await page.wait_for_timeout(2000)
        except playwright._impl._errors.TimeoutError:
            self.logger.warning(
                "Botón de ubicación no encontrado, continuando...")
            pass

        categories_urls = await self._get_categories(response, page)
        print(categories_urls)
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
                                          "wait_for_selector", cruzverdecl.SELECTOR_GET_ALL_PRODUCTS, timeout=90000),
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

    async def _get_categories(self, response: Response, page: Page):
        await page.wait_for_timeout(3000)
        button_categories = await page.wait_for_selector(
            cruzverdecl.SELECTOR_BUTTON_CATEGORIES)
        await page.wait_for_timeout(2000)
        if button_categories:
            await button_categories.click()

        self.logger.info("Obteniendo categorías y subcategorías...")
        await page.wait_for_timeout(2000)
        categories_urls = {}
        if hasattr(self, "category") and self.category:
            categories_elements = page.locator(cruzverdecl.XPATH_CATEGORY_NAME.replace(
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
            categories_elements = await page.query_selector_all(
                cruzverdecl.SELECTOR_GET_ALL_CATEGORIES)

            self.logger.info(
                "Categorías encontradas, procesando subcategorías...")

            for element in categories_elements:
                category_name = await element.inner_text()
                category_name = category_name.strip()
                categories_urls[category_name] = {}
                if category_name != 'Veterinaria':
                    # Inicializamos el diccionario para esta categoría

                    await element.click()
                    await page.wait_for_timeout(2000)

                    self.logger.info(
                        f"Procesando subcategorías para la categoría '{category_name}'...")
                    await self._expand_sub_categories(page)
                    await self._get_sub_categories(page, response, category_name, categories_urls)

        return categories_urls

    async def _expand_sub_categories(self, page: Page):
        """
        Expande iterativamente las subcategorías que necesitan ser clickeadas.
        Vuelve a buscar los elementos en cada iteración para manejar cambios en el DOM.
        """
        self.logger.info("Expandiendo todas las subcategorías necesarias...")
        await page.wait_for_timeout(3000)
        expandable_elements_locator = page.locator(
            cruzverdecl.SELECTOR_CLICK_SUB_CATEGORIES)
        count = await expandable_elements_locator.count()
        if count == 0:
            self.logger.info(
                "No se encontraron más subcategorías para expandir.")
            return
        for element in await expandable_elements_locator.element_handles():
            try:
                await element.click()
                self.logger.info("Elemento expandido.")

            except Exception as e:
                self.logger.warning(
                    f"Error al hacer clic en elemento para expandir: {e}. Puede que ya no sea necesario o haya otro problema.")

        self.logger.info("Expansión de subcategorías completada o detenida.")

    async def _get_sub_categories(self, page: Page, response: Response, category_name: str, categories_urls: dict):
        self.logger.info(
            f"Procesando subcategorías para la categoría '{category_name}'...")

        # Obtenemos todas las subcategorías para esta categoría específica
        sub_categories_elements = await page.query_selector_all(
            cruzverdecl.SELECTOR_GET_ALL_SUB_CATEGORIES)

        for sub_element in sub_categories_elements:
            # Obtenemos el nombre de la subcategoría dentro del elemento actual
            sub_category_links = await sub_element.query_selector_all(cruzverdecl.SELECTOR_GET_SUB_CATEGORIES_INSIDE)
            url_links = []
            if (len(sub_category_links) > 1):
                sub_category_name = await sub_category_links[0].inner_text()
                sub_category_name = sub_category_name.strip()

                for sub_cat in sub_category_links[1:]:
                    sub_category_name = await sub_cat.inner_text()
                    sub_category_name = sub_category_name.strip()
                    if 'Conoce más' in sub_category_name or 'Asesoría en vivo' in sub_category_name:
                        continue
                    href = await sub_cat.get_attribute('href')
                    if href:
                        if href.startswith("http"):
                            full_url = href
                        else:
                            full_url = response.urljoin(href)
                        url_links.append(full_url)
            else:
                sub_category_name = await sub_category_links[0].inner_text()
                sub_category_name = sub_category_name.strip()
                href = await sub_category_links[0].get_attribute('href')
                if href:
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = response.urljoin(href)
                    url_links.append(full_url)
            if url_links:
                categories_urls[category_name][sub_category_name] = url_links

    async def parse(self, response: Response, category, sub_category):
        page: Page = response.meta["playwright_page"]

        self.logger.info(
            f"Extrayendo productos de la categoría '{category}' y subcategoría '{sub_category}' en {response.url}")
        while True:
            await self._await_products_loaded(page)
            await page.wait_for_load_state("domcontentloaded")
            try:
                await page.wait_for_timeout(2000)
                await page.wait_for_selector(cruzverdecl.SELECTOR_GET_ALL_PRODUCTS, timeout=60000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                self.logger.warning("No se encontraron productos")
                break

            try:
                await page.wait_for_selector(cruzverdecl.SELECTOR_PRODUCT_NAME, timeout=60000)
                html_content = await page.content()
                scrapy_selector = scrapy.Selector(text=html_content)

                products = scrapy_selector.css(
                    cruzverdecl.SELECTOR_GET_ALL_PRODUCTS)
                for product_card in products:
                    try:
                        item = self.take_products_fields(
                            product_card, category, sub_category)
                    except Exception as e:
                        self.logger.error(
                            f"Saltando este producto. Error: {e} \n Produc card: {product_card}")
                        continue

                    item['comercial_name'] = cruzverdecl.NAME
                    item['comercial_id'] = cruzverdecl.ID
                    yield item
                if not await self.next_page(page):
                    break

            except Exception as e:
                self.logger.error(
                    f"Error encontrado para esta categoría {category} y sub {sub_category}:\n Error {e}")
            await page.wait_for_timeout(2000)

        await page.close()
        self.logger.info(
            f"Finalizada la extracción de productos para la categoría {category} y la subcategoría '{sub_category}'.")

    async def next_page(self, page: Page) -> bool:
        try:
            next_page_button: Locator = page.locator(
                cruzverdecl.XPATH_CLICK_NEXT_PAGE)
            if await next_page_button.count() > 0:
                await next_page_button.first.click()
                self.logger.info(
                    "Cargando más productos haciendo clic en el botón 'Cargar más'...")
                # Esperar a que se carguen los nuevos productos
                await page.wait_for_timeout(2000)
                return True
            else:
                self.logger.info(
                    "No hay más productos para cargar en esta subcategoría.")
                return False
        except playwright._impl._errors.TimeoutError as e:
            self.logger.error(f"Boton no encontrado, fin de la categoría")
            return False

    def take_products_fields(self, product_card: scrapy.Selector, category, sub_category):
        item = ScraperItem()
        price = product_card.xpath(cruzverdecl.XPATH_GET_PRICE).getall()
        if len(price) > 0:
            item['price'] = float(price[0].replace(
                '$', '').replace('.', '').strip())
        try:
            name = product_card.xpath(
                cruzverdecl.XPATH_GET_NAME).get().strip()
        except Exception as e:
            raise ValueError(
                f"Nombre de producto no encontrado ")
        item['name'] = name
        matches = re.findall(
            r'(\d+[\.,]?\d*)\s?((?:g|gr|ml|l|lt|kg|onz|mg|comprimido|lb|unidades|unideades|un|cm|m|u|grs|und|unds)\b)', name, re.IGNORECASE)
        if len(matches) > 0:
            value = matches[-1]
            item['total_unit_quantity'] = float(value[0].replace(',', '.'))
            item['unit_type'] = value[1].strip().lower()
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
                await page.wait_for_selector(cruzverdecl.SELECTOR_CONTAINER_PRODUCTS, timeout=60000)
            except Exception:
                self.logger.warning(
                    "El contenedor de productos no apareció. Saltando el scroll.")
                break
            current_height = await page.evaluate(f"document.querySelector('{cruzverdecl.SELECTOR_CONTAINER_PRODUCTS}').scrollHeight")

            if current_height == previous_height:
                self.logger.info(
                    "La altura del contenedor se ha estabilizado. Scroll finalizado para esta página.")
                await page.wait_for_timeout(2000)
                break

            try:
                previous_height = current_height
                self.logger.info("Haciendo scroll hasta el final...")
                await page.evaluate(f"window.scrollTo(0, {current_height})")
                await page.wait_for_timeout(2000)
            except Exception as e:
                self.logger.error(f"Error durante el scroll: {e}")
                break

    async def handle_error(self, failure):
        """Manejador de errores genérico. Cierra la página y loguea."""
        request = failure.request
        error_type = type(failure.value).__name__
        self.logger.error(
            f"[{self.name}] Error ({error_type}) en {request.url}: {failure.value}")

        page = request.meta.get("playwright_page")
        if page and not page.is_closed():
            self.logger.info(
                f"[{self.name}] Cerrando página por error en {request.url}")
            try:
                await page.close()
            except Exception as e_close:
                self.logger.warning(f"Error al cerrar página: {e_close}")
