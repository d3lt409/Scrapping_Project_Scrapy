
import asyncio
import sys

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

ADDONS = {}

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 3

FEED_EXPORT_ENCODING = "utf-8"

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

ITEM_PIPELINES = {
    'scraper.pipelines.PostgresPipeline': 300,
}

# Nivel de registro para la salida. Opciones: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
LOG_LEVEL = "INFO"

# --- CONFIGURACIÓN DE PLAYWRIGHT PARA AWS LAMBDA ---
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox", 
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor"
    ]
}


TELNETCONSOLE_ENABLED = False

DOWNLOAD_TIMEOUT = 5*60

# Aumenta el timeout por defecto de Playwright
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 90000  # 90 segundos

# Habilitar el middleware de reintentos (generalmente ya está activado por defecto)
RETRY_ENABLED = True

# Número de veces que se reintentará una petición fallida
RETRY_TIMES = 2

# Códigos de respuesta HTTP que activarán un reintento.
# 5xx son errores de servidor, 408 es timeout.
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408]

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
