import scrapy
import json
from scrapy.http import Response
from playwright.async_api import Page, Route
from scraper.items import ScraperItem


class JuriscolapiSpider(scrapy.Spider):
    name = "juriscolapi"

    # URL de la página web (no de la API)
    start_urls = [
        "https://www.suin-juriscol.gov.co/legislacion/normatividad.html#"]

    # URL de la API que descubriste
    api_url = "https://www.suin-juriscol.gov.co/CiclopeWs/Ciclope.svc/Find"

    # Body base (para la API)
    base_body = {
        "form": "normatividad#",
        "hitlist": "legis",
        "estado_documento": "Vigente",
        "fields": "tipo|numero|anio|sector|entidad_emisora|estado_documento|epigrafe",
        "tipo": "Leyes",
        "sector": "Salud y Protección Social",
        "coleccion": "legis",
        "usuario": "web",
        "passwd": "dA4qd1uUGLLtM6IK+1xiVQ==",
        "pagina": "next"
    }

    # --- 1. Inicio con Playwright ---

    async def start(self):
        """
        Inicia con Playwright para cargar la página,
        realizar la búsqueda y capturar la petición del primer 'next'.
        """
        self.logger.info(
            "Iniciando Playwright para la configuración inicial de SUIN...")
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_context="default_persistent"  # Usa contexto persistente
                ),
                callback=self.perform_initial_search,
                errback=self.handle_error  # Un manejador de error genérico
            )

    async def perform_initial_search(self, response: Response):
        """
        Usa Playwright para configurar la búsqueda, hacer clic en 'Buscar'
        y luego en 'Siguiente' para capturar la cookie.
        """
        page: Page = response.meta["playwright_page"]

        try:
            # --- 1. Configurar la Búsqueda ---
            # (Ajusta estos selectores a los de la página real)
            self.logger.info(
                "Configurando filtros de búsqueda en la página...")

            more_options = await page.wait_for_selector("#alternar-respuesta-ej1")
            await more_options.click()  # Expande opciones si es necesario

            # Ejemplo: Seleccionar Tipo "Leyes"
            # (El body ya lo tiene, pero si la página lo necesita para activar el botón...)
            await page.select_option("select#sector", label="Tecnologías de la Información y de las Comunicaciones")

            # Ejemplo: Seleccionar Estado "Vigente"
            await page.select_option("select#estado_documento_Otros", label="Vigente")

            # Variable para almacenar las cookies capturadas
            captured_cookies = []

            # Ejemplo: Clic en el botón "Buscar"
            # (Necesitas el selector real del botón de búsqueda)
            BUSCAR_BUTTON_SELECTOR = "input#buscar"  # ¡AJUSTA ESTO!
            async with page.expect_response(lambda resp: self.api_url in resp.url and resp.request.method == "POST") as resp_ctx:
                await page.click(BUSCAR_BUTTON_SELECTOR)

            response_api = await resp_ctx.value

            # Retrieve the response body
            response_body = await response_api.json()  # Or .text() for raw text
            self.logger.info(f"POST Response Body: {response_body}")
            self.logger.info(
                "Búsqueda inicial realizada. Esperando resultados...")

            # Espera un momento para asegurar que la intercepción se complete
            await page.wait_for_timeout(5000)
            await page.close()  # Cierra Playwright, ya no lo necesitamos

            # --- 4. Lanzar el Spider de API ---
            if not captured_cookies:
                self.logger.error(
                    "No se pudieron capturar las cookies. Abortando.")
                return

            self.logger.info(
                f"Cookies capturadas exitosamente: {captured_cookies}")

            # Prepara el body para la paginación de la API
            api_body = self.base_body.copy()
            api_body["cookies"] = response_body.get('cookies', [])

            print("API BODY:", api_body)

            # # Lanza la primera petición DIRECTA a la API (sería la pág 2)
            # yield scrapy.Request(
            #     url=self.api_url,
            #     method='POST',
            #     body=json.dumps(api_body),
            #     headers={'Content-Type': 'application/json;charset=UTF-8'},
            #     callback=self.parse_api_response,  # El parser de la API
            #     meta={'api_body': api_body}  # Pasamos el body para reusarlo
            # )

        except Exception as e:
            self.logger.error(f"Error durante la fase de Playwright: {e}")
            await page.close()

    # --- 2. Lógica del Spider de API (Rápido) ---

    async def parse_api_response(self, response: Response):
        """
        Parsea la respuesta JSON de la API, extrae items y maneja la paginación.
        """
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(
                f"Error al decodificar JSON de la API: {response.url}")
            return

        # 1. Extraer los documentos (items)
        docs = data.get('docs', [])
        self.logger.info(
            f"API: Obtenidos {len(docs)} documentos (índices {data.get('startIndex')} a {data.get('endIndex')})...")

        for doc in docs:
            item = self.parse_document_item(doc)
            item[
                'url_documento'] = self.get_url_path(doc.get('homeTitle', ''), doc.get('path', ''))
            yield item

        # 2. Manejar la Paginación de la API
        view_is_end = data.get('viewIsEnd', 'yes')

        # Obtenemos las *nuevas* cookies de esta respuesta
        cookies_from_response = data.get('cookies')

        if view_is_end == 'no' and cookies_from_response:
            self.logger.info(
                "API: 'viewIsEnd' es 'no'. Solicitando siguiente página...")

            # Obtenemos el body anterior y actualizamos las cookies
            next_page_body = response.meta.get(
                'api_body', self.base_body.copy())
            # ¡Actualizamos con las cookies de la respuesta!
            next_page_body['cookies'] = cookies_from_response

            yield scrapy.Request(
                url=self.api_url,
                method='POST',
                body=json.dumps(next_page_body),
                headers={'Content-Type': 'application/json;charset=UTF-8'},
                callback=self.parse_api_response,
                # Pasamos el body actualizado
                meta={'api_body': next_page_body}
            )
        else:
            self.logger.info(
                "API: Fin de la paginación ('viewIsEnd' es 'yes').")

    def get_url_path(self, home_title, path):
        """Genera la URL del documento basado en el título y la ruta."""
        return f"https://www.suin-juriscol.gov.co/viewDocument.asp?{home_title}={path}"

    def parse_document_item(self, doc):
        """Convierte el objeto 'doc' del JSON en un ScraperItem."""
        item = ScraperItem()  # Asegúrate de que tu item tenga estos campos

        item['titulo'] = doc.get('title', 'N/A')
        item['path_id'] = doc.get('path', 'N/A')

        for field in doc.get('fields', []):
            name = field.get('name')
            value = field.get('value', '').strip()

            if name == 'tipo':
                item['tipo_norma'] = value
            elif name == 'numero':
                item['numero_norma'] = value
            elif name == 'anio':
                item['anio_norma'] = value
            elif name == 'sector':
                item['sector'] = value
            elif name == 'entidad_emisora':
                item['entidad_emisora'] = value
            elif name == 'estado_documento':
                item['estado'] = value
            elif name == 'epigrafe':
                item['descripcion'] = value

        return item

    async def handle_error(self, failure):
        """Manejador de error genérico."""
        self.logger.error(
            f"Error procesando {failure.request.url}: {failure.value}")
        page = failure.request.meta.get("playwright_page")
        if page and not page.is_closed():
            self.logger.info(
                f"Cerrando página por error en {failure.request.url}")
            await page.close()
