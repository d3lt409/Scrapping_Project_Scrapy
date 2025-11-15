import scrapy
from playwright.sync_api import Page
from scrapy.http import Response
from scraper.items import JuriscolItem


class JuriscolapicompletedSpider(scrapy.Spider):
    name = "juriscolapicompleted"
    pais = 'legislacion_col_temp'
    allowed_domains = ["www.suin-juriscol.gov.co"]
    start_urls = [
        "https://www.suin-juriscol.gov.co/legislacion/normatividad.html"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.JuriscolPipeline': 201,
        }
    }

    async def start(self):

        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "default_persistent"
                },
                callback=self.parse
            )

    async def parse(self, response):

        self.cur.execute(
            f"SELECT id, documento_url FROM public.{self.pais} where norma_completa  = ''")
        self.results = self.cur.fetchall()
        for res in self.results:
            documento_url = res['documento_url'].replace("?Resolucion=", "?ruta=") if 'Resolucion' in res['documento_url'] else res['documento_url'].replace(
                "?Leyes=", "?ruta=") if 'Leyes' in res['documento_url'] else res['documento_url'].replace("?Decretos=", "?ruta=") if 'Decretos' in res['documento_url'] else res['documento_url']
            documento_id = res['id']
            yield scrapy.Request(
                url=documento_url,
                callback=self.parse_document,
                meta={'documento_id': documento_id,
                      "last_url": res['documento_url']}
            )
        self.logger.info("Finalizada la generación de requests.")

    def parse_document(self, response: Response):
        documento_id = response.meta['documento_id']
        item = JuriscolItem()
        if response.status != 200:
            item['id'] = documento_id
            item["action_type"] = "update"
            item['norma_completa'] = None
            item['documento_url'] = response.meta['last_url']
            self.logger.error(
                f"Error al acceder al documento {response.url}: Status {response.status}")
            yield item
            return

        item['id'] = documento_id
        item["action_type"] = "update"
        text = response.xpath(
            "//body/div[@style and not(contains(@style, 'hidden')) and not(@class='slider')]//text()").getall()
        item['norma_completa'] = ' '.join(text).strip()
        item['documento_url'] = response.url
        yield item
