import scrapy
from playwright.async_api import Page
from scrapy import signals
from scraper.items import JuriscolItem
from .constants import jurisper


class JurispercompletedSpider(scrapy.Spider):
    name = "jurispercompleted"
    allowed_domains = ["spij.minjus.gob.pe"]

    pais = 'legislacion_per'

    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.JurisperPipeline': 201,
        },
        # --- ¡AÑADE ESTO! ---
        # Limita Scrapy a 4 peticiones concurrentes en total
        'CONCURRENT_REQUESTS': 1,
        # Limita a 4 peticiones a la vez para este dominio
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        # (Opcional) Un pequeño delay entre peticiones
        'DOWNLOAD_DELAY': 6
    }

    def __init__(self, *args, **kwargs):
        super(JurispercompletedSpider, self).__init__(*args, **kwargs)
        # Configuración de la conexión a la base de datos
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from scraper.config import (
            DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT,
            DB_SSL_MODE, DB_SSL_PATH
        )

        def _connect():
            hostname = DB_HOST
            username = DB_USER
            password = DB_PASSWORD
            database = DB_NAME
            port = DB_PORT

            # Preparar argumentos SSL según configuración
            ssl_args = {}
            if DB_SSL_MODE:
                ssl_args['sslmode'] = DB_SSL_MODE
            # Solo incluir sslrootcert si el modo requiere verificación
            if DB_SSL_MODE in ('verify-ca', 'verify-full') and DB_SSL_PATH:
                ssl_args['sslrootcert'] = DB_SSL_PATH

            connection = psycopg2.connect(
                host=hostname,
                user=username,
                password=password,
                dbname=database,
                port=port,
                **ssl_args
            )

            cur = connection.cursor(cursor_factory=RealDictCursor)
            cur.execute("SET search_path TO public;")

            cur = cur
            connection = connection

            return connection, cur

        self.conn, self.cur = _connect()
        self.cur.execute(
            f"SELECT id, documento_url FROM public.{self.pais} where norma_completa is NULL")
        self.start_urls = self.cur.fetchall()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        Este método de Scrapy nos permite conectar
        la señal spider_closed.
        """
        spider = super(JurispercompletedSpider, cls).from_crawler(
            crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self):
        """
        Este método será llamado automáticamente cuando 
        la araña termine, para cerrar la conexión.
        """
        self.logger.info("Araña cerrada. Cerrando conexión de base de datos.")
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    # ... (el resto de tus métodos, como start_requests, parse, etc.) ...

    def start_requests(self):
        self.logger.info(f"Número de leyes a procesar: {len(self.start_urls)}")
        for law in self.start_urls:
            yield scrapy.Request(
                law['documento_url'],
                meta={
                    "documento_id": law['id'],
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",
                        "timeout": 60000
                    }

                },
                callback=self.parse
            )

    async def parse(self, response):
        try:
            self.logger.info(f"Parsing law details para: {response.url}")
            item = JuriscolItem()
            page: Page = response.meta["playwright_page"]
            await page.wait_for_selector(jurisper.SELECTOR_COMPLETE_LAW, timeout=30000)
            # 4. Crear un NUEVO Selector con ese HTML
            page_content = scrapy.Selector(text=await page.content())
            norma_completa = page_content.xpath(
                jurisper.XPATH_GET_COMPLETE_LAW_TEXT).getall()
            norma_completa = ' '.join([text.strip()
                                       for text in norma_completa]).strip()
            if "derogada" in norma_completa.lower():
                self.logger.warning("Norma derogada, continuando")
                return
            date = page_content.xpath(jurisper.XPATH_GET_DATE_PUBLISHED).get()
            if not date:
                self.logger.warning(f"No se encontró 'date' en {response.url}")
                if page:
                    await page.close()
                # Asigna un valor por defecto para evitar que 'split' falle
                return
            ano = date.split(" ")[-1].strip()
            emisor = page_content.xpath(jurisper.XPATH_GET_EMISOR).get()
            if not emisor:
                self.logger.warning(
                    f"No se encontró 'emisor' en {response.url}")
                emisor = "No especificado"
                if page:
                    await page.close()
                return

            # Llenar el item
            item["id"] = response.meta.get("documento_id")
            item['ano'] = ano
            item['emisor'] = emisor
            item['norma_completa'] = norma_completa
            item["action_type"] = "update"
            yield item
        except Exception as e:
            self.logger.error(f"Error procesando {response.url}, error {e}")
        finally:
            self.logger.info(f"Cerrando página para: {response.url}")
            if page:
                await page.close()
