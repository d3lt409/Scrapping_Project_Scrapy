import asyncio
import sys
import os

# Detectar proyecto actual usando el directorio de trabajo
current_path = os.getcwd()

if 'scraper_vea' in current_path:
    # Configuración específica para PlazaVea
    BOT_NAME = "scraper_vea"
    SPIDER_MODULES = ["scraper_vea.spiders"]
    NEWSPIDER_MODULE = "scraper_vea.spiders"
    PROJECT_NAME = "PlazaVea"
else:
    # Configuración específica para Jumbo (por defecto)
    BOT_NAME = "scraper"
    SPIDER_MODULES = ["scraper.spiders"]
    NEWSPIDER_MODULE = "scraper.spiders"
    PROJECT_NAME = "Jumbo"

# Configuración general compartida
ADDONS = {}

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 1  # Forzar 1 request a la vez para evitar conflictos de Playwright
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 5  # Incrementado para evitar conflictos de Playwright
RANDOMIZE_DOWNLOAD_DELAY = 0.3  # Reducido para menos variabilidad

# Cookies and sessions
COOKIES_ENABLED = True

# Cache settings
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000

# Auto throttling settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2  # Incrementado
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# CONFIGURACIÓN PARA PROCESAMIENTO SECUENCIAL DE MÚLTIPLES CATEGORÍAS
SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.ScrapyPriorityQueue'
REACTOR_THREADPOOL_MAXSIZE = 1

# Configuración específica de Playwright para estabilidad
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-web-security"]
}

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

# Middlewares compartidos
SPIDER_MIDDLEWARES = {
    'shared_middlewares.SharedSpiderMiddleware': 543,
}

DOWNLOADER_MIDDLEWARES = {
    'shared_middlewares.SharedDownloaderMiddleware': 543,
}

# Pipeline unificado - se adapta automáticamente
ITEM_PIPELINES = {
    'shared_pipeline.PostgresPipeline': 300,
}

# Playwright configuration
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Playwright browser settings
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,
    "slow_mo": 100,
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

# Feed exports
FEED_EXPORT_ENCODING = "utf-8"

# Windows specific configuration
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Logging
LOG_LEVEL = 'INFO'