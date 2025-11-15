import itertools
import scrapy
from .constants import jurisper
from scraper.items import JuriscolItem
from scrapy_playwright.page import PageMethod
from scrapy.http import Response
from playwright.async_api import Page


class JurisperSpider(scrapy.Spider):
    name = "jurisper"
    allowed_domains = ["spij.minjus.gob.pe"]
    start_urls = {
        "salud": ["https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682789"],
        # "Tecnología": ["https://www.gob.pe/institucion/pcm/colecciones/147-normativa-sobre-transformacion-digital"]
    }
    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.JurisperPipeline': 201,
        }
    }

    async def start(self):
        for category, urls in self.start_urls.items():
            for url in urls:
                yield scrapy.Request(
                    url,
                    meta={
                        "playwright": True,
                        "category": category,
                        "playwright_include_page": True,
                        "playwright_context": "default_persistent",
                        "playwright_page_goto_kwargs": {
                            "wait_until": "domcontentloaded",
                            "timeout": 60000
                        }
                    },
                    # 1. CAMBIO: Llamamos a parse_salud directamente.
                    # 'orquestrator' ha sido eliminado/fusionado.
                    callback=self.parse_salud
                )

    # 2. CAMBIO: 'orquestrator' desaparece.
    # 'parse_salud' es ahora el "dueño" de la página.

    async def parse_salud(self, response: Response):
        self.logger.info("Parsing Salud category (Dueño de la página)")
        page: Page = response.meta["playwright_page"]

        try:
            # --- Esperas iniciales (como en el 'orquestrator') ---
            self.logger.info(
                "ParseSalud: Esperando DOM content loaded...")
            await page.wait_for_load_state("domcontentloaded", timeout=65000)
            self.logger.info("ParseSalud: Esperando selector de ley...")
            await page.wait_for_selector(
                jurisper.SELECTOR_COMPLETE_LAW, timeout=60000)
            self.logger.info(
                "ParseSalud: ¡Contenido inicial listo! Extrayendo links...")

            # --- Lógica de extracción de links (de 'parse_salud') ---
            page_content = scrapy.Selector(text=await page.content())
            all_links = page_content.xpath(jurisper.XPATH_GET_ALL_LAWS_SALUD)

            epigrafo_selectors = all_links[0::2]
            norma_selectors = all_links[1::2]

            self.logger.info(
                f"Total laws (pairs) found: {len(epigrafo_selectors)}")

            # 3. CAMBIO: Guardamos todos los links en una lista primero
            all_pairs_data = []
            sector = "Salud"

            for epi_selector, law_selector in zip(epigrafo_selectors, norma_selectors):
                content_law = epi_selector.xpath("text()").get()
                if content_law is None:
                    content_law = ""

                epigrafe = content_law.strip()
                url = law_selector.xpath("@href").get()

                if not url:
                    self.logger.warning(
                        f"No URL for epigrafe: {epigrafe}. Skipping.")
                    raise ValueError("No URL found")

                if not url.startswith("http"):
                    url = "https://spij.minjus.gob.pe" + url

                law = law_selector.xpath("text()").get().strip()
                numero = law.split("Nº")[-1].strip()
                tipo = ""
                if "decreto" in law.lower():
                    tipo = "DECRETO"
                elif "ley" in law.lower():
                    tipo = "LEY"
                elif "resolución" in law.lower():
                    tipo = "RESOLUCIÓN"
                else:
                    self.logger.warning(
                        f"Tipo no identificado en: {law}. Saltando.")
                    continue

                # Guardamos los datos para usarlos después
                all_pairs_data.append({
                    "url": url,
                    "meta_data": {
                        "sector": sector,
                        "tipo": tipo,
                        "epigrafe": epigrafe,
                        "documento_url": url,
                        "numero": numero
                    }
                })

            self.logger.info(f"Se extrajeron {len(all_pairs_data)} links. "
                             "Comenzando bucle de navegación en serie...")

            # 4. CAMBIO: Hacemos un NUEVO bucle para navegar y scrapear
            #    Esto procesará una ley a la vez
            for i, pair in enumerate(all_pairs_data):
                url = pair["url"]
                meta = pair["meta_data"]

                self.logger.info(
                    f"Procesando Norma {i+1}/{len(all_pairs_data)}: Navegando a {url}")

                # Navegamos la página
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(8000)
                # Llamamos a nuestra función helper para extraer
                item = await self.parse_law_details_helper(page, meta)

                if item:
                    yield item
                else:
                    self.logger.warning(
                        f"No se pudo procesar el item de {url}")

        except Exception as e:
            self.logger.error(f"Error fatal en parse_salud: {e}")
        finally:
            # 5. CAMBIO: El 'finally' ahora está aquí.
            # Se ejecutará solo después de que el bucle de navegación termine.
            self.logger.info(
                "ParseSalud: Trabajo finalizado. Cerrando página.")
            await page.close()

    # 6. CAMBIO: Nueva función 'helper'. NO es un callback de Scrapy.

    async def parse_law_details_helper(self, page: Page, meta: dict) -> JuriscolItem | None:
        """
        Función helper que recibe la RESPUESTA ya navegada y los METADATOS,
        y devuelve un Item.
        """
        self.logger.info(f"Helper: Extrayendo detalles de {page.url}")
        item = JuriscolItem()
        item.update(meta)  # Carga todos los metadatos
        self.logger.info(f"Helper: Metadatos cargados: {item}")
        try:
            # Esperamos que cargue el contenido del detalle
            self.logger.info(
                "Helper: Esperando que aparezca la fecha (selector de detalle)...")
            await page.wait_for_selector(
                "//*[@id='bodyContenido']//p[last()]/font",
                timeout=60000
            )
            self.logger.info(
                "Helper: ¡Selector de detalle encontrado! La página cambió.")
            await self._await_products_loaded(page)
        except Exception as e:
            self.logger.error(
                f"Timeout esperando el detalle de la ley: {page.url} - {e}")
            return None  # Devolvemos None si falla
        await page.wait_for_timeout(2000)  # Pequeña espera extra
        page_content = scrapy.Selector(text=await page.content())
        with open(f"debug_jurisper{item['numero']}.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
        date = page_content.xpath(jurisper.XPATH_GET_DATE_PUBLISHED).get()
        if not date:
            self.logger.warning(f"No se encontró 'date' en {page.url}")
            raise ValueError("No se encontró 'date'")

        item['ano'] = date.split(" ")[-1].strip()

        emisor = page_content.xpath(jurisper.XPATH_GET_EMISOR).get()
        if not emisor:
            self.logger.warning(f"No se encontró 'emisor' en {page.url}")
            raise ValueError("No se encontró 'emisor'")
        else:
            item['emisor'] = emisor.strip()

        item['estado'] = "Vigente"
        norma_completa = page_content.xpath(
            jurisper.XPATH_GET_COMPLETE_LAW).getall()
        item['norma_completa'] = ' '.join(norma_completa).strip()

        return item

    async def _await_products_loaded(self, page: Page):
        # Espera inicial para asegurarse de que la página esté completamente cargada
        previous_height = -1
        while True:
            try:
                await page.wait_for_selector(jurisper.SELECTOR_COMPLETE_LAW, timeout=60000)
            except Exception:
                self.logger.warning(
                    "El contenedor de productos no apareció. Saltando el scroll.")
                break
            current_height = await page.evaluate(f"document.querySelector('{jurisper.SELECTOR_COMPLETE_LAW}').scrollHeight")

            if current_height == previous_height:
                self.logger.info(
                    "La altura del contenedor se ha estabilizado. Scroll finalizado para esta página.")
                await page.wait_for_timeout(2000)
                break

            try:
                previous_height = current_height
                self.logger.info("Haciendo scroll hasta el final...")
                await page.evaluate(f"window.scrollTo(0, {current_height})")
                await page.wait_for_timeout(2000)
            except Exception as e:
                self.logger.error(f"Error durante el scroll: {e}")
                break
