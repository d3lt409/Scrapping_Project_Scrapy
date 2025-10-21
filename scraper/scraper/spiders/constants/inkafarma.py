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

import re

# Regex para extraer números del total de productos
REGEX_TOTAL_PRODUCTOS = re.compile(r'Encontramos\s+(\d+)\s+productos?', re.IGNORECASE)

# Regex para limpiar precios
REGEX_PRECIO = re.compile(r'[\s\$\,]')
REGEX_SOLO_NUMEROS = re.compile(r'[^\d\.]')

# Regex para extraer cantidad de presentación
REGEX_CANTIDAD_PRESENTACION = re.compile(r'(\d+(?:\.\d+)?)\s*(ml|mg|g|kg|l|un|unidades?|caps?|comp|tab)', re.IGNORECASE)

# Selector para el h3 que muestra el conteo de productos
SELECTOR_PRODUCT_COUNT_H3 = "h3.m-0.heading-1"
# Selector para el menú de categorías
SELECTOR_CATEGORIES_MENU_BUTTON = "div.content-category"
# Selector para los elementos de subcategoría
SELECTOR_SUBCATEGORIES = "div.list-option.label.ng-star-inserted"
# Selector para el span dentro de subcategoría (para texto)
SELECTOR_SUBCATEGORY_SPAN = "div.list-option.label.ng-star-inserted span"

# ============================================================================
# SELECTORES PARA MENÚ DESPLEGABLE CON 3 COLUMNAS (CORREGIDOS CON ESTRUCTURA REAL)
# ============================================================================

# Selector para hacer hover al header de categorías
SELECTOR_MENU_HOVER = "div.content-category"

# Selectores reales basados en la estructura encontrada en el HTML
# InkaFarma usa un sistema de enlaces con href="/categoria/" para navegación
SELECTOR_CATEGORIA_LINKS = "a[href*='/categoria/']"

# Selectores alternativos para encontrar el menú de navegación
SELECTOR_NAV_CONTAINER = "fp-navigation-header-responsive nav, nav.navigation-header"
SELECTOR_SWIPER_CONTAINER = "swiper-container"
SELECTOR_SWIPER_SLIDES = "swiper-slide"

# Selectores para elementos de categoría en el swiper
SELECTOR_CATEGORY_SLIDES = "swiper-slide .category-swiper-item"
SELECTOR_CATEGORY_LINKS_IN_SLIDES = "swiper-slide a.router-link"

# Selectores para el menú lateral (sidenav)
SELECTOR_SIDENAV = "fp-categories-of-menu-responsive"
SELECTOR_SIDENAV_CONTAINER = "mat-sidenav-container"

# Ya que el menú hover no funciona como esperábamos, usaremos los enlaces directos
# que encontramos en la estructura real de la página
FALLBACK_CATEGORY_LINKS = [
    "/categoria/inka-packs",
    "/categoria/farmacia", 
    "/categoria/salud",
    "/categoria/mama-y-bebe",
    "/categoria/nutricion-para-todos",
    "/categoria/dermatologia-cosmetica",
    "/categoria/cuidado-personal",
    "/categoria/belleza",
    "/categoria/limpieza-y-cuidado-para-el-hogar"
]


CATEGORIAS_CON_SUBCATEGORIAS = {
    "cupones-promocionales": [
        "cupon-inka30",
        "cupon-inka15"
    ],
    "inka-packs": [
        "packs-de-adulto-mayor",
        "packs-de-farmacia",
        "packs-de-nutricion-y-bienestar",
        "packs-de-dermatologia-cosmetica",
        "packs-para-el-cuidado-infantil",
        "packs-de-cuidado-personal",
        "packs-de-nutricion-infantil",
        "packs-de-belleza"
    ],
    "precios-mas-bajos": [
        "tu-sonrisa-merece-totaldent"
    ],
    "farmacia": [
        "nos-preocupamos-por-tu-salud",
        "consulta-medica",
        "malestar-de-la-tos-con-flema",
        "dolor-generalizado",
        "resfriado-comun",
        "cuidado-respiratorio",
        "colicos-menstruales",
        "malestar-estomacal",
        "malestar-general-y-fiebre",
        "herbolario",
        "oidos",
        "cuidado-muscular-y-articular",
        "lo-mejor-de-pg-health"
    ],
    "salud": [
        "vitaminas-y-complementos",
        "soluciones-fisiologicas",
        "sistema-urinario",
        "sistema-sanguineo",
        "sistema-oseo-y-articulaciones",
        "sistema-nervioso",
        "sistema-digestivo",
        "sistema-respiratorio",
        "sistema-cardiovascular",
        "productos-galenicos",
        "problemas-generales",
        "preparados-estomatologicos",
        "otologicos",
        "optica",
        "oftalmologicos",
        "nutricion",
        "infecciones-y-otros",
        "dispositivos-quirurgicos",
        "hormonas",
        "cuidado-muscular-y-articular",
        "cuidado-dermatologico",
        "cuidado-de-la-mujer",
        "antineoplasicos-e-inmunomoduladores",
        "antibacterianos-para-uso-sistemico"
    ],
    "mama-y-bebe": [
        "vitaminas-y-suplementos",
        "todo-en-ninet",
        "promociones-en-nutricion-infantil",
        "toallitas-humedas",
        "soporte-para-embarazo",
        "panales-para-bebe",
        "maquillaje-para-ninas",
        "formula-para-bebes",
        "dormitorio",
        "cuidado-de-bebes-y-perfumeria",
        "cuidado-corporal-para-mama",
        "accesorios-de-lactancia",
        "actividades",
        "accesorios-de-cuidado-infantil",
        "vestimenta",
        "promociones-para-el-cuidado-infantil",
        "jugueteria"
    ],
    "nutricion-para-todos": [
        "promociones-en-suplementos-y-vitaminas",
        "vitaminas",
        "suplementos-nutricionales",
        "snacks-y-piqueos",
        "minerales",
        "multivitaminicos",
        "nutricion-pensada-en-ti-y-tu-familia",
        "fitness-y-deportivos"
    ],
    "dermatologia-cosmetica": [
        "promociones-en-dermocosmetica",
        "cuidado-capilar",
        "fotoprotector",
        "dermatologia-pediatrica",
        "tratamientos-corporales",
        "otros-productos",
        "tratamiento-facial"
    ],
    "cuidado-personal": [
        "promociones-en-cuidado-e-higiene-personal",
        "cuidado-intimo",
        "bano",
        "cuidado-de-la-piel",
        "jabones",
        "cuidado-del-cabello",
        "cuidado-de-manos-y-pies",
        "cuidado-bucal",
        "afeitado",
        "bienestar-sexual"
    ],
    "belleza": [
        "promociones-en-belleza",
        "electrobelleza",
        "cosmeticos",
        "cuidado-facial",
        "cremas-hidratantes",
        "fragancias",
        "tintes-para-cabello",
        "accesorios",
        "depilacion",
        "bloqueadores-solares"
    ],
    "limpieza-y-cuidado-para-el-hogar": [
        "limpieza-del-hogar",
        "papel-higienico-y-toallas",
        "insecticidas",
        "aromatizantes",
        "accesorios-de-cocina",
        "baterias-y-pilas"
    ],
    "cuidado-del-cabello": [
        "cuidado-y-belleza-superior",
        "cuidado-masculino",
        "tintes",
        "accesorios",
        "cuidado-profesional",
        "shampoo-y-acondicionador",
        "tratamientos"
    ],
    "adulto-mayor": [
        "promociones-para-el-adulto-mayor",
        "incontinencia",
        "cuidado-bucal",
        "nutricion-adulto",
        "vitaminas-para-adultos"
    ],
    "dispositivos-medicos": [
        "vaporizador",
        "test-covid-pruebas-rapidas",
        "test-de-embarazo",
        "termometros",
        "tensiometros",
        "respirometro",
        "ortopedia",
        "oximetros",
        "nebulizadores",
        "lampara-infrarroja",
        "glucometros",
        "botiquin",
        "articulos-de-proteccion",
        "equipos-medicos",
        "sistema-cardiovascular",
        "problemas-generales"
    ],
    "productos-naturales": [
        "sistema-renal-reproductor",
        "sistema-locomotor",
        "sistema-digestivo",
        "sistema-circulatorio",
        "productos-naturales",
        "infusiones-naturales",
        "dietas",
        "antioxidantes",
        "alimentos-naturales"
    ],
    "deportes": [
        "nutricion-deportiva",
        "zona-fitness",
        "maquinas-deportivas",
        "accesorios-deportivos",
        "natacion",
        "equipos-de-box",
        "scooter",
        "bicicletas",
        "ropa-derpotiva-para-mujer",
        "crossfit"
    ],
    "peru-pasion": [
        "nutricion",
        "higiene-y-cuidado-personal",
        "dispositivos-ortopedicos",
        "belleza-y-estetica"
    ],
    "nuevas-categorias": [
        "promociones-marketplace",
        "tecnologia-y-accesorios",
        "nutricion-adultos",
        "mundo-infantil",
        "moda-mujer",
        "mascotas",
        "limpieza-para-tu-hogar",
        "hogar-y-decoracion",
        "electrohogar",
        "dormitorio",
        "belleza-y-accesorios",
        "accesorios-para-autos",
        "videojuegos-y-consolas"
    ]
}

# Template de URL para categorías con subcategorías
CATEGORIA_SUBCATEGORIA_URL_TEMPLATE = "https://inkafarma.pe/categoria/{categoria}/{subcategoria}"
