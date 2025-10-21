

def handle_error(spider, failure):
    """Manejar errores de requests incluyendo timeouts"""
    request = failure.request
    category_index = request.meta.get("category_index", "unknown")
    original_url = request.meta.get("original_url", request.url)

    # Obtener información de la URL
    url_parts = original_url.split('/')
    if len(url_parts) >= 2:
        categoria = url_parts[-2].replace('-', ' ').title()
        subcategoria = url_parts[-1].replace('-', ' ').title()
    else:
        categoria = "Unknown"
        subcategoria = "Unknown"

    if "TimeoutError" in str(failure.type):
        spider.logger.warning(
            f"Timeout en Request #{category_index}: {categoria} > {subcategoria}")
        spider.logger.warning(f"URL afectada: {original_url}")

        # Intentar un reintento con timeout más largo
        retry_count = request.meta.get('retry_count', 0)
        if retry_count < 2:  # Máximo 2 reintentos
            spider.logger.info(
                f"Reintentando Request #{category_index} (intento {retry_count + 1})")
            retry_request = request.replace(
                meta={
                    **request.meta,
                    'retry_count': retry_count + 1,
                    'playwright_page_goto_kwargs': {
                        "wait_until": "domcontentloaded",
                        "timeout": 45000  # Timeout más largo para reintentos
                    }
                }
            )
            return retry_request
        else:
            spider.logger.error(
                f"Máximo de reintentos alcanzado para Request #{category_index}: {categoria} > {subcategoria}")
    else:
        spider.logger.error(
            f"Error en Request #{category_index}: {categoria} > {subcategoria} - {failure}")
