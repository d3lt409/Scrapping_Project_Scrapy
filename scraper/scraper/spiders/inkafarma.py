import scrapy


class InkafarmaSpider(scrapy.Spider):
    name = "inkafarma"
    allowed_domains = ["inkafarma.pe"]
    start_urls = ["https://inkafarma.pe/"]

    def parse(self, response):
        pass
