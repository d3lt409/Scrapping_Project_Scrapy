import scrapy
from scrapy.linkextractors import LinkExtractor
import re
import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import ScraperItem
from scraper.spiders.constants import cruzverde
from scrapy.http import Response
from playwright.async_api import Page

class CruzverdeSpider(scrapy.Spider):
    name = "cruzverde"
    allowed_domains = ["www.cruzverde.com.co"]
    start_urls = ["https://www.cruzverde.com.co/"]
    
    def start_requests(self):
        for url in self.start_urls:
            
            yield scrapy.Request(
                url,
                meta=dict(playwright=True, playwright_include_page=True,
                          playwright_page_methods=[
                              PageMethod(
                                  "wait_for_selector", cruzverde.SELECTOR_CITY_ACEPTAR),
                          ],
                          playwright_page_goto_kwargs={
                              "wait_until": "domcontentloaded",
                              "timeout": 60000
                          }
                          ),

                callback=self.orchestrator,
                cb_kwargs={}
            )
            
    async def orchestrator(self, response: Response):
        page: Page = response.meta["playwright_page"]
        
        try:
            button_city = await page.wait_for_selector(cruzverde.SELECTOR_CITY_ACEPTAR, timeout=15000)
            await button_city.click()
            await page.wait_for_timeout(2000)  # Espera adicional para asegurarse de que la acción se complete
            list_category_button = await page.wait_for_selector(cruzverde.SELECTOR_CLICK_CATEGORIES, timeout=15000)
            await list_category_button.click()
            await page.wait_for_timeout(2000)
        except Exception as e:
            self.logger.warning(f"No se pudo aceptar la ciudad para {response.url}. Procediendo con scrapeo directo. Error: {e}")
            await page.wait_for_timeout(2000)
        await page.wait_for_selector(cruzverde.SELECTOR_GET_ALL_CATEGORIES, timeout=15000)
        get_all_categories = await page.query_selector_all(cruzverde.SELECTOR_GET_ALL_CATEGORIES)
        for category in get_all_categories:
            category_name = await category.inner_text()
            if category_name in cruzverde.LIST_CATEGORIES:
                await category.click()
                await page.wait_for_timeout(2000)  # Espera adicional para asegurarse de que la acción se complete
                await page.wait_for_selector(cruzverde.SELECTOR_SEARCH_SUBCATEGORY, timeout=15000)
                subcategories = await page.query_selector_all(cruzverde.SELECTOR_SEARCH_SUBCATEGORY)
                for subcategory in subcategories:
                    category_link = await subcategory.get_attribute('href')
                    if category_link and category_link.startswith('http'):
                        category_link = category_link # Asegurarse de que el enlace es absoluto
                    elif category_link and not category_link.startswith('http'):
                        category_link = response.urljoin(category_link)
                    sub_category_name = await subcategory.inner_text()
                    print(f"Navegando a la subcategoría: {sub_category_name} ({category_name})")
                    yield scrapy.Request(
                        url=category_link,
                        meta=dict(playwright=True, playwright_include_page=True,
                                    playwright_page_methods=[
                                        PageMethod(
                                            "wait_for_selector", cruzverde.SELECTOR_CONTAINER_PRODUCTS),
                                    ],
                                    playwright_page_goto_kwargs={
                                        "wait_until": "domcontentloaded",
                                        "timeout": 60000
                                    }
                                    ),
                        callback=self.parse_category,
                        cb_kwargs={'category_name': category_name, 'sub_category_name': sub_category_name}
                    )
    async def parse_category(self, response: Response, category_name, sub_category_name):
        page: Page = response.meta["playwright_page"]
        page_number = 1
        while True:
            async for item in self.save_products_count(page, page_number, response, category_name, sub_category_name):
                yield item
            await page.wait_for_timeout(2000) 
            next_page_button = page.locator(
                f"xpath={cruzverde.XPATH_CLICK_NEXT_PAGE}")

            if await next_page_button.count() > 0:
                print("Botón 'Siguiente' encontrado. Navegando a la siguiente página...")
                await page.wait_for_timeout(2000) 
                await next_page_button.first.click()
                print("Clic en el botón 'Siguiente' realizado.")
                await page.wait_for_selector(cruzverde.SELECTOR_GET_ALL_PRODUCTS, timeout=60000)
                page_number += 1
            else:
                print("No se encontró el botón 'Siguiente'. Fin de la categoría.")
                break
        await page.close()
        
    async def await_products_loaded(self, page: Page):
        await page.wait_for_selector(cruzverde.SELECTOR_GET_ALL_PRODUCTS, timeout=15000)
        previous_height = -1
        while True:
            try:
                await page.wait_for_selector(cruzverde.SELECTOR_CONTAINER_PRODUCTS, timeout=6000)
            except Exception:
                self.logger.warning("El contenedor de productos no apareció. Saltando el scroll.")
                break
            current_height = await page.evaluate(f"selector => document.querySelector(selector).scrollHeight",cruzverde.SELECTOR_CONTAINER_PRODUCTS)

            print(f"Altura del contenedor: {current_height}px")

            if current_height == previous_height:
                print(
                    "La altura del contenedor se ha estabilizado. Scroll finalizado para esta página.")
                break

            previous_height = current_height

            print("Haciendo scroll hasta el final...")
            await page.evaluate(f"window.scrollTo(0, {current_height})")
            await page.wait_for_timeout(2000)
            
    async def save_products_count(self, page:Page, page_number, response: Response, category, sub_category):
        print(f"Scrapeando página {page_number} de '{response.url}'...")
        await self.await_products_loaded(page)
        html_content = await page.content()
        scrapy_selector = scrapy.Selector(text=html_content)
        for product_card in scrapy_selector.css(cruzverde.SELECTOR_GET_ALL_PRODUCTS):
            yield self.take_products_fields(product_card, category, sub_category)

    def take_products_fields(self, product_card: scrapy.Selector, category, sub_category):

        item = ScraperItem()

        name = product_card.xpath(cruzverde.XPATH_GET_NAME).get().strip()
        item['name'] = name
        matches = re.findall(
            r'(\d+[\.,]?\d*)\s?((?:g|gr|ml|l|kg|unidades|un|cm|m|u|grs|und|unds|tabletas|tableta|mg)\b)', name.lower(), re.IGNORECASE)
        if matches:
            value = matches[-1]
            item['total_unit_quantity'] = float(value[0].replace(
                '.', '').replace(',', '.'))
            item['unit_type'] = value[1]
        else:
            item["total_unit_quantity"] = 1
            item['unit_type'] = 'un'
        item['category'] = category
        item['sub_category'] = sub_category
        item['comercial_name'] = cruzverde.NAME

        item['comercial_id'] = cruzverde.ID

        price_text = product_card.xpath(cruzverde.XPATH_GET_PRICE).get()
        if not price_text:
            print(f"Precio no encontrado para el producto: {name}, sub_categoria {sub_category}. Asignando precio 0.")
            exit()
        price = price_text.strip().replace(
            '$', '').replace('.', '').replace(",", ".").strip()
        price = re.sub(r'[^\d.]', '', price)  
        item['price'] = float(price)

        unit_price_text = product_card.xpath(
            cruzverde.XPATH_GET_UNIT_PRICE).get()
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