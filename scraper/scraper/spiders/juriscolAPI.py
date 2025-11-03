import scrapy
import json
import copy
import requests
from scrapy.http import Response
from playwright.async_api import Page, Route
from scraper.items import JuriscolItem
from .constants.juriscol import TIPOS_NORMA, SECTORES_PRIORITARIOS, ESTADOS_VIGENCIA_PRIORITARIOS


import datetime


class JuriscolapiSpider(scrapy.Spider):
    name = "juriscolapi"

    start_urls = ["https://www.suin-juriscol.gov.co/legislacion/normatividad.html#"]
    api_url = "https://www.suin-juriscol.gov.co/CiclopeWs/Ciclope.svc/Find"

    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 0.5,
    }

    def __init__(self, *args, **kwargs):
        only_sector = kwargs.pop('only_sector', None)
        super().__init__(*args, **kwargs)
        self.tipos = list(TIPOS_NORMA.values())
        self.sectores = [only_sector] if only_sector else SECTORES_PRIORITARIOS
        self.vigencias = ESTADOS_VIGENCIA_PRIORITARIOS
        self.combos = [
            (sector, tipo, vig)
            for sector in self.sectores
            for tipo in self.tipos
            for vig in self.vigencias
        ]
        self.combo_index = 0

    def parse(self, response):
        # Redirige a start_requests para usar Playwright
        for req in self.start_requests():
            yield req

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_context="default_persistent"
                ),
                callback=self.perform_initial_search
            )

    async def perform_initial_search(self, response):
        page = response.meta["playwright_page"]
        async with page.expect_response(lambda r: self.api_url in r.url) as resp_ctx:
            await page.click("input#buscar")
        api_resp = await resp_ctx.value
        data = await api_resp.json()
        cookies = data.get("cookies", [])
        await page.close()
        if not cookies:
            self.logger.error("❌ No cookies")
            return
        self.cookies = cookies
        self.logger.info(f"✅ Cookies capturadas")
        # Lanzar la primera combinación
        for req in self.request_next_combo():
            yield req

    def request_next_combo(self):
        if self.combo_index >= len(self.combos):
            self.logger.info("🎯 Todas las combinaciones completadas.")
            return
        sector, tipo, vig = self.combos[self.combo_index]
        body = {
            "form": "normatividad#",
            "hitlist": "legis",
            "estado_documento": vig,
            "fields": "tipo|numero|anio|sector|entidad_emisora|estado_documento|epigrafe",
            "tipo": tipo,
            "sector": sector,
            "coleccion": "legis",
            "usuario": "web",
            "passwd": "dA4qd1uUGLLtM6IK+1xiVQ==",
            "cookies": self.cookies,
            "pagina": "next"
        }
        self.logger.info(f"\n🔎 [INICIO] {sector} | {tipo} | {vig}")
        yield scrapy.Request(
            url=self.api_url,
            method="POST",
            body=json.dumps(body),
            headers={"Content-Type": "json"},
            callback=self.parse_api_response,
            meta={"sector": sector, "tipo": tipo, "vig": vig, "body": body},
        )

    async def parse_api_response(self, response):
        sector = response.meta["sector"]
        sector = response.meta["sector"]
        tipo = response.meta["tipo"]
        vig = response.meta["vig"]
        body = response.meta["body"]

        data = json.loads(response.text)
        docs = data.get("docs", [])
        hit = data.get("hitCount")
        start = data.get("startIndex")
        end = data.get("endIndex")
        endflag = data.get("viewIsEnd")

        self.logger.info(f"📄 {sector}|{tipo}|{vig} → {len(docs)} docs [{start}-{end}/{hit}]")

        for d in docs:
            yield self.parse_document_item(d)

        # Si la API indica que terminó, no se sigue paginando
        if endflag == "yes":
            self.logger.info(f"✅ FIN combo {sector}|{tipo}|{vig}")
            self.combo_index += 1
            for req in self.request_next_combo():
                yield req
            return

        # Si no terminó, sigue paginando enviando siempre "next"
        body_next = dict(body)
        body_next["pagina"] = "next"
        self.logger.info(f"➡️ Siguiente página: pagina = 'next'")
        yield scrapy.Request(
            self.api_url,
            method="POST",
            body=json.dumps(body_next),
            headers={"Content-Type": "json"},
            callback=self.parse_api_response,
            meta=response.meta,
            dont_filter=True
        )

    def parse_document_item(self, doc):
        item = JuriscolItem()
        for field in doc.get('fields', []):
            name = field.get('name')
            value = field.get('value', '').strip()
            if name == 'tipo':
                item['tipo'] = value
            elif name == 'numero':
                item['numero'] = value
            elif name == 'anio':
                item['ano'] = value
            elif name == 'sector':
                item['sector'] = value
            elif name == 'entidad_emisora':
                item['emisor'] = value
            elif name == 'estado_documento':
                item['estado'] = value
            elif name == 'epigrafe':
                item['epigrafe'] = value
        item['documento_url'] = self.get_url_path(doc.get('homeTitle', ''), doc.get('path', ''))
        item['result_datetime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return item

    def get_url_path(self, home_title, path):
        return f"https://www.suin-juriscol.gov.co/viewDocument.asp?{home_title}={path}"

    async def handle_error(self, failure):
        self.logger.error(f"Error procesando {failure.request.url}: {failure.value}")
        page = failure.request.meta.get("playwright_page")
        if page and not page.is_closed():
            self.logger.info(f"Cerrando página por error en {failure.request.url}")
            await page.close()
