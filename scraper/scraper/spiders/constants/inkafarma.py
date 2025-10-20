# Categorias de inkafarma
CATEGORIAS = [
    "inka-packs",
    "farmacia",
    "salud",
    "mama-y-bebe",
    "nutricion-para-todos",
    "dermatologia-cosmetica",
    "cuidado-personal",
    "belleza",
    "limpieza-y-cuidado-para-el-hogar",
    "cuidado-del-cabello-1",
    "adulto-mayor-1",
    "dispositivos-medicos",
    "productos-naturales-1"
]

# Url base y plantilla de URL para categorías en InkaFarma
BASE_URL = "https://inkafarma.pe/"
CATEGORIA_URL_TEMPLATE = "https://inkafarma.pe/categoria/{categoria}"

# Información comercial
COMERCIAL_ID = "20608430301"
COMERCIAL_NAME = "InkaFarma"

# ============================================================================
# SELECTORES CSS/XPATH PARA SCRAPING
# ============================================================================

# ============================================================================
# SELECTORES REALES DE INKAFARMA (Actualizados con estructura real encontrada)
# ============================================================================

# Selector para total de productos (buscar en header/título de la página)
SELECTOR_TOTAL_PRODUCTOS = "fp-categories-landing h1, fp-categories-landing h2, fp-product-view-component h1, fp-product-view-component h2"

# Contenedor principal de productos (el card real que contiene toda la información)
SELECTOR_PRODUCTOS_CONTAINER = "fp-filtered-product-list > fp-product-large"

# Selector de cada producto individual - CORREGIDO basado en estructura real
SELECTOR_PRODUCTO_CARD = "fp-product-small-category"  # Este es el contenedor real de cada producto

# Selectores específicos para datos del producto usando fp-* components - CORREGIDOS
SELECTOR_PRODUCTO_NOMBRE = "fp-product-name span"  # Nombre dentro del span
SELECTOR_PRODUCTO_PRESENTACION = "fp-product-description span"  # Descripción dentro del span
SELECTOR_PRODUCTO_PRECIO = "fp-product-card-price span:last-child"  # Último span (precio actual)
SELECTOR_PRODUCTO_PRECIO_ANTERIOR = "fp-product-card-price span:first-child"  # Primer span (precio anterior si existe)
SELECTOR_PRODUCTO_LINK = "a"

# XPath selectores (más robustos para Playwright)
XPATH_PRODUCTO_CARD = "//fp-product-small-category"
XPATH_PRODUCTO_NOMBRE = ".//fp-product-name//span"
XPATH_PRODUCTO_PRESENTACION = ".//fp-product-description//span" 
XPATH_PRODUCTO_PRECIO = ".//fp-product-card-price//span[last()]"  # Último span

# Selectores alternativos más específicos
SELECTOR_PRODUCTO_CARD_ALT = "[id] fp-link a div"
SELECTOR_PRECIO_CONTAINER = "fp-product-card-price div div div"

# Selectores para información adicional
SELECTOR_BREADCRUMB = "nav.breadcrumb a"
SELECTOR_CATEGORIA = "nav.breadcrumb a:nth-last-child(2)"

# Selectores para scroll infinito
SELECTOR_LOADING = "div.loading, .spinner"
SELECTOR_LOAD_MORE_BUTTON = "button.load-more, .load-more-btn"

# ============================================================================
# CONFIGURACIÓN DE SCROLL Y TIMEOUTS
# ============================================================================

# Configuración para scroll infinito
SCROLL_PAUSE_TIME = 2  # Segundos entre scrolls
MAX_SCROLL_ATTEMPTS = 50  # Máximo número de intentos de scroll
SCROLL_HEIGHT_STEP = 1000  # Píxeles por scroll

# Timeouts para esperas
TIMEOUT_PAGE_LOAD = 30000  # 30 segundos
TIMEOUT_SELECTOR = 15000   # 15 segundos
TIMEOUT_SCROLL = 5000      # 5 segundos

# ============================================================================
# EXPRESIONES REGULARES PARA PARSING
# ============================================================================

import re

# Regex para extraer números del total de productos
REGEX_TOTAL_PRODUCTOS = re.compile(r'Encontramos\s+(\d+)\s+productos?', re.IGNORECASE)

# Regex para limpiar precios
REGEX_PRECIO = re.compile(r'[\s\$\,]')
REGEX_SOLO_NUMEROS = re.compile(r'[^\d\.]')

# Regex para extraer cantidad de presentación
REGEX_CANTIDAD_PRESENTACION = re.compile(r'(\d+(?:\.\d+)?)\s*(ml|mg|g|kg|l|un|unidades?|caps?|comp|tab)', re.IGNORECASE)

