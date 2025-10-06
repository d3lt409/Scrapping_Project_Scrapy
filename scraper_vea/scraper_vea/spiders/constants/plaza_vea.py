# Constantes para el spider de PlazaVea
# Categorías del mercado con sus URLs base

CATEGORIAS_MERCADO = {
    "frutas-y-verduras": [
        "frutas",
        "verduras"
    ],
    "carnes-aves-y-pescados": [
        "pollo",
        "res",
        "cerdo",
        "pescados-y-mariscos",
        "pavo-pavita-y-otras-aves",
        "enrollados"
    ],
    "desayunos": [
        "cafe-e-infusiones",
        "cereales",
        "modificadores-de-leche",
        "mermeladas-mieles-y-dulces",


    ],
    "lacteos-y-huevos": [
        "leche",
        "mantequilla-y-margarina",
        "yogurt",
        "huevos"

    ],
    "quesos-y-fiambres": [
        "quesos-blandos",
        "quesos-semiduros",
        "quesos-duros",
        "quesos-procesados",
        "embutidos",
        "jamonadas-y-jamones-cocidos",
        "jamonadas-y-jamones-cocidos",
        "salames-y-salchichones",
        "otros-fiambres",
        "tablas-y-piqueos"
    ],
    "congelados": [
        "hamburguesas-nuggets-y-apanados",
        "panes-pastas-bocaditos-y-salsas",
        "enrollados",
        "helados-y-postres"
    ],
    "abarrotes": [
        "arroz",
        "aceite",
        "azucar-y-endulzantes",
        "menestras",
        "conservas",
        "fideos-pastas-y-salsas",
        "salsas-cremas-y-condimentos",
        "comidas-instantaneas",
        "galletas-y-golosinas",
        "chocolateria",
        "snacks-y-piqueos"
    ],
    "panaderia-y-pasteleria": [
        "pan-de-la-casa",
        "pan-envasado",
        "pasteleria",
        "panetones",
        "postres",
        "reposteria",
        "tortillas-y-masas"
    ],
    "pollo-rostizado-y-comidas-preparadas": [
        "pollo-rostizado",
        "comidas-preparadas",
        "cremas-salsas-y-condimentos-a-granel",
        "pizzas-y-pastas-frescas",
        "tamales-y-humitas"
        
    ],
    "bebidas" : [
        "gaseosas",
        "aguas",
        "jugos-y-otras-bebidas",
        "bebidas-funcionales"
    ],
    "vinos-licores-y-cervezas": [
        "licores",
        "vinos",
        "espumantes",
        "cervezas",
        "cigarros",
        "hielo"
    ],
    "limpieza" : [
        "cuidado-de-la-ropa",
        "cuidado-del-hogar",
        "papel-para-el-hogar",
        "limpieza-de-bano",
        "limpieza-de-cocina",
        "limpieza-de-calzado",
        "accesorios-de-limpieza"
    ],
    "cuidado-personal-y-salud" : [
        "cuidado-del-cabello",
        "higiene-personal",
        "cuidado-bucal",
        "proteccion-femenina",
        "proteccion-adulta",
        "afeitado",
        "depilacion",
        "bienestar-sexual",
        "packs-de-regalo",
        "salud",
        "vitaminas-y-nutricion"
    ],
    "belleza" : [
        "proteccion-solar",
        "cuidado-facial",
        "cuidado-de-la-piel-corporal",
        "maquillaje-y-cosmeticos",
        "perfumes-y-fragancias",
    ],
    "bebe-e-infantil": [
        "panales-y-toallitas-para-bebe",
        "alimentacion-del-bebe",
        "cuidado-y-aseo-del-bebe"
    ],
    "mascotas": [
        "comida-para-perros",
        "salud-e-higiene-para-perros",
        "accesorios-para-perros",
        "otras-mascotas",
        "comida-para-gatos",
        "salud-e-higiene-para-gatos",
        "accesorios-para-gatos"
    ],
    "packs": [
        "packs-vinos-licores-y-cervezas",
        "packs-lacteos-y-huevos",
        "packs-abarrotes",
        "packs-desayunos",
        "packs-panaderia-y-pasteleria",
        "packs-pollo-rostizado-y-comidas-preparadas",
        "packs-bebidas",
        "packs-bebe-e-infantil",
        "packs-cuidado-personal-y-salud",
        "packs-limpieza",
        "packs-quesos-y-fiambres"
    ],
    "mercado-saludable": [
        "alimentos-organicos",
        "cuidado-personal-sostenible",
        "cosmetica-natural",
        "desayunos-organicos",
        "snacks-organicos",
        "vitaminas-y-suplementos-organicos"
    ],
    "tecnologia": [
        "televisores",
        "computo",
        "telefonia",
        "videojuegos",
        "audio",
        "fotografia",
        "cine-en-casa",
        "cigarros-electronicos"
    ],
    "electrohogar": [
        "refrigeracion",
        "lavado",
        "cocinas",
        "climatizacion",
        "electrodomesticos-de-cocina",
        "electrodomesticos-del-hogar",
        "cuidado-personal",
        "herramientas-electricas"
    ]
}

# URL base para construir URLs de categorías
BASE_URL = "https://www.plazavea.com.pe"
CATEGORIA_URL_TEMPLATE = "/{categoria}/{subcategoria}"

# XPaths para extraer datos
XPATH_CONTAINER = '//*[@id="undefined-60"]/div/div[10]/div/div[2]/div[1]'
XPATH_PRODUCTS = '//div[@class="Showcase__details"]'
XPATH_PRODUCT_NAME = './/button[@class="Showcase__name"]/text()'
XPATH_PRODUCT_PRICE = './/div[@class="Showcase__salePrice"]/@data-price'
XPATH_PRODUCT_UNIT_REFERENCE = './/div[@class="Showcase__units-reference"]/text()'

# XPaths para paginación corregidos
XPATH_PAGINATION = '//div[@class="pagination"]//div[@class="pagination__nav"]'
XPATH_ACTIVE_PAGE = '//span[contains(@class, "pagination__item") and contains(@class, "page-number") and contains(@class, "active")]/text()'
XPATH_NEXT_PAGE_BUTTON = '//span[contains(@class, "pagination__item") and contains(@class, "page-number") and not(contains(@class, "active"))]'
XPATH_ALL_PAGES = '//span[contains(@class, "pagination__item") and contains(@class, "page-number")]/text()'

# Selectores para esperar carga
SELECTOR_PRODUCTS_CONTAINER = 'div[class*="Showcase__details"]'
SELECTOR_PAGINATION = 'div.pagination__nav'