# Scrapy settings for scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import asyncio
import sys


BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings (optimizado para procesamiento secuencial robusto)
CONCURRENT_REQUESTS = 1  # Una sola request activa para procesamiento secuencial
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # Una request por dominio
DOWNLOAD_DELAY = 0.5  # Delay reducido para velocidad

# Timeout settings (optimizado para estabilidad)
DOWNLOAD_TIMEOUT = 120  # 120 segundos para descargas complejas
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_TIMEOUT = 120000  # 120 segundos para Playwright
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 150000  # 2.5 minutos para navegación

# Retry settings (más agresivo para robustez)
RETRY_ENABLED = True
RETRY_TIMES = 5  # Más reintentos
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 520, 521, 523]

# AutoThrottle deshabilitado para control manual
AUTOTHROTTLE_ENABLED = False

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "scraper.middlewares.ScraperSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "scraper.middlewares.ScraperDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    "scraper.pipelines.ScraperPipeline": 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"


DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
}

# Configuraciones de Playwright para manejar timeout
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-blink-features=AutomationControlled",
        "--window-size=1920,1080",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ],
    "slow_mo": 0  # Sin ralentización artificial
}

PLAYWRIGHT_CONTEXTS = {

    "persistent": {

        "user_data_dir": "./context",  # will be a persistent context

    },

}

# Configuración de timeouts extendidos para estabilidad
DOWNLOAD_TIMEOUT = 120  # 120 segundos
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 150000  # 2.5 minutos

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

ITEM_PIPELINES = {
    'scraper.pipelines.PostgresPipeline': 300,
    'scraper.pipelines.JuriscolPipeline': 301,
    'scraper.pipelines.JurisperPipeline': 302,
}

# País para la tabla de base de datos
DATABASE_COUNTRY = 'peru'

# Logging configuration to suppress DEBUG logs from scrapy-playwright
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'scrapy-playwright': {
            'level': 'INFO',
        },
    },
}

LOG_LEVEL = 'INFO'

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
