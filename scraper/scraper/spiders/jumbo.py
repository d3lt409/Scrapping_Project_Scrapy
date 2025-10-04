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
    # + jumbo.START_URLS_ELECTRO + jumbo.START_URLS_PHARMACY
    start_urls = jumbo.START_URLS_SUPERMARKET[0:2]

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(playwright=True, playwright_include_page=True,
                          playwright_page_methods=[
                              PageMethod(
                                  "wait_for_selector", jumbo.SELECTOR_LOAD_PRODUCTS),
                              PageMethod(
                                  "evaluate", "window.scrollBy(0, document.body.scrollHeight)")
                          ],
                          playwright_page_goto_kwargs={
                              "wait_until": "domcontentloaded",
                              "timeout": 60000
                          }
                          ),

                callback=self.parse_category
            )

    async def parse_category(self, response: Response):
        page: Page = response.meta["playwright_page"]
        page_number = 1
        while True:
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

            next_page_button = page.locator(
                f"xpath={jumbo.XPATH_CLICK_BUTTON}")

            if await next_page_button.count() > 0:
                print("Botón 'Siguiente' encontrado. Navegando a la siguiente página...")
                time.sleep(2)  # Pequeña pausa antes de hacer clic
                await next_page_button.first.click()
                print("Clic en el botón 'Siguiente' realizado.")
                await page.wait_for_selector(jumbo.SELECTOR_LOAD_PRODUCTS, timeout=60000)
                page_number += 1
            else:
                print("No se encontró el botón 'Siguiente'. Fin de la categoría.")
                break
        await page.close()

    def take_products_fields(self, product_card: scrapy.Selector, category, sub_category):

        item = ScraperItem()

        name = product_card.xpath('.//h3/span//text()').get().strip()
        item['name'] = name
        matches = re.findall(
            r'(\d+[\.,]?\d*)\s?((?:g|gr|ml|l|kg|unidades|un|cm|m|u|grs|und|unds)\b)', name, re.IGNORECASE)
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
        await page.wait_for_selector(jumbo.SELECTOR_LOAD_PRODUCTS, timeout=15000)
        previous_height = -1
        while True:
            current_height = await page.evaluate(f"document.querySelector('{jumbo.SELECTOR_CONTAINER_PRODUCTS}').scrollHeight")

            print(f"Altura del contenedor: {current_height}px")

            if current_height == previous_height:
                print(
                    "La altura del contenedor se ha estabilizado. Scroll finalizado para esta página.")
                break

            previous_height = current_height

            print("Haciendo scroll hasta el final...")
            await page.evaluate(f"window.scrollTo(0, {current_height})")
            # Espera crucial para dar tiempo a que se carguen y rendericen los nuevos productos
            time.sleep(2)
