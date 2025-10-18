from scrapy.utils.reactor import install_reactor
install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")

import os
import json
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from scrapy.utils.defer import deferred_to_future
import asyncio

# Importa la clase de tu araña.
from scraper.spiders.TestSpider import TestSpider  # Cambia esto por el nombre de tu araña

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"
os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"
os.environ["CHROME_PATH"] = "/ms-playwright/chromium-1187/chrome-linux/chrome"
os.environ["PYPPETEER_HOME"] = "/tmp"
os.environ["XDG_CACHE_HOME"] = "/tmp"
os.environ["TMPDIR"] = "/tmp"
os.environ["HOME"] = "/tmp"


def lambda_handler(event, context):
    """
    Esta es la función que AWS Lambda ejecutará.
    'event' contiene los datos de entrada (si los hay).
    'context' contiene información sobre el entorno de ejecución.
    """
    print("Iniciando ejecución de la función Lambda para el scraper...")
    
    print("Playwright browsers path:", os.environ.get("PLAYWRIGHT_BROWSERS_PATH"))
    
    
    try:
    # Creamos una función asíncrona interna para contener nuestra lógica
        async def main():
            print("¡Función Lambda iniciada! Reactor asyncio instalado.")
            
            settings = get_project_settings()
            configure_logging(settings)
            
            print("Iniciando ejecución del scraper...")
            
            runner = CrawlerRunner(settings)
            
            # Le decimos a Scrapy que empiece a correr la araña
            deferred = runner.crawl(TestSpider)  # Cambia TestSpider por el nombre de tu araña
            
            # Usamos el "traductor" para que asyncio pueda esperar a que Twisted termine
            await deferred_to_future(deferred)

            print("Ejecución del scraper finalizada.")
            # Devolvemos una respuesta simple para indicar que la ejecución fue exitosa
            return {
                'statusCode': 200,
                'body': json.dumps('Scraping finalizado exitosamente!')
            }
            
        asyncio.run(main())
    except Exception as e:
        print(f"Ocurrió un error durante la ejecución del scraper: {e}")
        return {
                'statusCode': 500,
                'body': json.dumps({"msg":'Scraping finalizado con errores!', "error": str(e)})
            }

    