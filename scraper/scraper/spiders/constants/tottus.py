# Categorías principales del mercado Tottus (URLs exactas extraídas del HTML real)
CATEGORIAS_MERCADO = {
    "Abarrotes": {  
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16827/Abarrotes"
    },
    "Desayunos": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16065/Desayunos"
    },
    "Marca tottus": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16067/Marca-Tottus"
    },
    "Carnes": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16076/Carnes"
    },
    "Lácteos y quesos": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16061/Lacteos"
    },
    "Huevos y Fiambres": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16060/Huevos-y-Fiambres"
    },
    "Pescados y Mariscos": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16074/Pescados-y-Mariscos"
    },
    "Productos Congelados": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16062/Productos-Congelados"
    },
    "Frutas y Verduras": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16050/Frutas-y-Verduras"
    },
    "Bebidas alcoholicas": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16069/Bebidas-Alcoholicas"
    },
    "Confitería y Snacks": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16834/Confiteria-y-Snacks"
    },
    "Gaseosas, aguas y jugos": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16068/Bebidas"
    },
    "Desayunos": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG17627/Desayunos"
    },
    "Panadería": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16071/Panaderia"
    },
    "Pastelería": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16063/Pasteleria"
    },
    "Dulces y galletas":{
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16059/Confiteria"
    },
    "Reposteria": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16056/Reposteria"
    },
    "Platos preparados": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16064/Platos-Preparados"
    },
    "Mundo Parrillero": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16081/Parrilla"
    },
    "Snacks y frutos secos": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16058/Snacks"
    },
    "Cervezas": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16070/Cervezas"
    },
    "Mascotas": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16055/Mundo%20Mascotas"
    },
    "Cuidado Personal": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16072/Cuidado-Personal"
    },
    "Bebés y Niños": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16828/Bebes-y-Ninos"
    },
    "Limpieza y Hogar": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16831/Limpieza"
    },
    "Belleza": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG16057/Belleza"
    },
    "Tecnología": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG48292/Tecnologia"
    },
    "Electrohogar": {
        "url": "https://www.tottus.com.pe/tottus-pe/lista/CATG48293/Electrohogar"
    }

}

# URL base para construir URLs de categorías
BASE_URL = "https://www.tottus.com.pe"
CATEGORIA_URL_TEMPLATE = "https://www.tottus.com.pe/tottus-pe/categoria/{categoria_name}"

# Información comercial
COMMERCIAL_ID = "20508565934"
COMMERCIAL_NAME = "tottus"

# XPaths para elementos del navegador (botón de categorías)
XPATH_CATEGORY_BUTTON = '//div[contains(@class, "CategoryButton-module_container-top-menu")]'
XPATH_CATEGORY_WRAPPER = '//div[contains(@class, "CategoryButton-module_categoryWrapper")]'
XPATH_NAVIGATION_MENU = '//div[contains(@class, "SiSNavigationMenu-module_container")]'
XPATH_SIDE_MENU = '//div[contains(@class, "SideMenu-module_navigation")]'

# XPaths para extraer datos de productos (basados en la estructura real de Tottus)
XPATH_CONTAINER = '//div[contains(@class, "search-results-4-grid")]'
XPATH_PRODUCTS = '//div[contains(@class, "search-results-4-grid grid-pod")]'
XPATH_PRODUCT_NAME = './/b[contains(@id, "testId-pod-displaySubTitle")]//text()'
XPATH_PRODUCT_PRICE = './/li[@data-internet-price]//span[contains(@class, "copy10")]//text() | .//li[@data-internet-price]/@data-internet-price'
XPATH_PRODUCT_UNIT_REFERENCE = './/div[contains(@class, "pod-subtitle-unit")]//text()'
XPATH_PRODUCT_IMAGE = './/img[contains(@id, "testId-pod-image")]/@src'
XPATH_PRODUCT_LINK = './/a[contains(@class, "pod-link")]/@href'

# XPaths específicos para nuevos campos de Tottus
XPATH_PRODUCT_ID = './/a/@data-key'
XPATH_PRODUCT_BRAND = './/b[contains(@class, "pod-title")]//text()'
XPATH_PRODUCT_SELLER = './/b[contains(@id, "testId-pod-displaySellerText")]//text()'
XPATH_PRODUCT_CATEGORY_CODE = './/a/@data-category'
XPATH_PRODUCT_SPONSORED = './/a/@data-sponsored'

# XPaths para precios y descuentos
XPATH_PRODUCT_CURRENT_PRICE = './/li[@data-internet-price]/@data-internet-price'
XPATH_PRODUCT_ORIGINAL_PRICE = './/li[@data-normal-price]/@data-normal-price'
XPATH_PRODUCT_DISCOUNT = './/span[contains(@id, "testId-Pod-badges")]//text()'
XPATH_PRODUCT_CURRENCY = './/li[@data-internet-price]//span[contains(@class, "copy10")]//text()[contains(., "S/")]'

# XPaths para imágenes
XPATH_PRODUCT_MAIN_IMAGE = './/picture[1]//img/@src'
XPATH_PRODUCT_SECONDARY_IMAGE = './/picture[2]//img/@src'

# XPaths para información de envío
XPATH_PRODUCT_SHIPPING = './/ul[contains(@class, "shipping-details")]//span[contains(@class, "copy4")]//text()'

# XPaths para paginación (basados en estructura HTML real de Tottus)
XPATH_PAGINATION = '//div[contains(@class, "css-1l4w6pd")]//div[contains(@class, "chakra-stack")]'
XPATH_ACTIVE_PAGE = '//button[contains(@class, "pagination-item") and contains(@class, "active")]//p//text()'
XPATH_NEXT_PAGE_BUTTON = '//button[@id="testId-pagination-bottom-arrow-right"]'
XPATH_PREVIOUS_PAGE_BUTTON = '//button[@id="testId-pagination-bottom-arrow-left"]'
XPATH_SPECIFIC_PAGE_BUTTON = '//button[@id="testId-pagination-bottom-button{}"]'
XPATH_ALL_PAGES = '//button[contains(@id, "testId-pagination-bottom-button") and contains(@class, "pagination-item")]//p//text()'

# Selectores CSS para esperar carga (actualizados para Tottus)
SELECTOR_PRODUCTS_CONTAINER = 'div[id="testId-searchResults-products"]'
SELECTOR_PAGINATION = 'div.css-1l4w6pd div.chakra-stack'
SELECTOR_PAGINATION_BUTTON = 'button[class*="pagination-item"]'
SELECTOR_LOADING = 'div[class*="loading"]'

# URLs de prueba para testing (con formato real de Tottus)
TEST_URLS = [
    "https://www.tottus.com.pe/tottus-pe/lista/CATG16839/Frutas-y-Verduras",
    "https://www.tottus.com.pe/tottus-pe/lista/CATG16835/Comestibles",
    "https://www.tottus.com.pe/tottus-pe/lista/CATG16076/Carnes"
]

def get_all_urls():
    """
    Devuelve una lista de todas las URLs de categorías principales
    """
    return [data["url"] for data in CATEGORIAS_MERCADO.values()]

def get_category_urls():
    """
    Devuelve las URLs principales de categorías (alias de get_all_urls)
    """
    return get_all_urls()

def get_category_names():
    """
    Devuelve una lista con los nombres de todas las categorías
    """
    return list(CATEGORIAS_MERCADO.keys())

def get_category_by_name(name):
    """
    Devuelve la información de una categoría específica por nombre
    """
    return CATEGORIAS_MERCADO.get(name)

# ============================================================================
# FUNCIONES UTILITARIAS PARA CATEGORIZACIÓN
# ============================================================================

def get_category_name_from_url(url):
    """
    Extrae el nombre de la categoría desde la URL de Tottus
    
    Args:
        url (str): URL de la categoría de Tottus
        
    Returns:
        str: Nombre de la categoría extraído de la URL
    """
    # Buscar en CATEGORIAS_MERCADO cuál categoría tiene esta URL
    for category_name, category_data in CATEGORIAS_MERCADO.items():
        if category_data["url"] == url.split('?')[0]:  # Remover parámetros de query
            return category_name
    
    # Si no encuentra coincidencia directa, intentar extraer del final de la URL
    try:
        # URL format: https://www.tottus.com.pe/tottus-pe/lista/CATGXXXXX/Nombre-Categoria
        url_parts = url.split('/')
        if len(url_parts) >= 2:
            category_part = url_parts[-1].split('?')[0]  # Remover parámetros
            # Convertir de formato URL a nombre legible
            category_name = category_part.replace('-', ' ').replace('%20', ' ')
            return category_name
    except Exception:
        pass
    
    return "General"

def get_main_category_from_tottus_category(tottus_category_name):
    """
    Determina la categoría principal basándose en el nombre de categoría de Tottus
    
    Args:
        tottus_category_name (str): Nombre de la categoría de Tottus
        
    Returns:
        str: Categoría principal asignada
    """
    if not tottus_category_name:
        return "mercado"
    
    category_lower = tottus_category_name.lower()
    
    # Clasificación por palabras clave
    if any(keyword in category_lower for keyword in ['bebe', 'bebé', 'niño', 'niña', 'infantil']):
        return "bebes_y_ninos"
    elif any(keyword in category_lower for keyword in ['mascota', 'perro', 'gato', 'animal']):
        return "mascotas"
    elif any(keyword in category_lower for keyword in ['limpieza', 'detergente', 'hogar', 'casa']):
        return "limpieza_y_hogar"
    elif any(keyword in category_lower for keyword in ['belleza', 'cosmetico', 'maquillaje']):
        return "cuidado_personal"
    elif any(keyword in category_lower for keyword in ['cuidado', 'personal', 'higiene', 'salud']):
        return "cuidado_personal"
    elif any(keyword in category_lower for keyword in ['tecnologia', 'electronico', 'digital', 'celular', 'tablet']):
        return "tecnologia"
    elif any(keyword in category_lower for keyword in ['electrodomestico', 'electrohogar', 'electrico', 'cocina', 'refrigerador']):
        return "electrohogar"
    elif any(keyword in category_lower for keyword in ['alcohol', 'cerveza', 'vino', 'licor', 'pisco']):
        return "bebidas_alcoholicas"
    else:
        return "mercado"  # Default para productos de alimentación
