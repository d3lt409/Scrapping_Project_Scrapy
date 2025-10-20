START_URLS_SUPERMARKET_1 = [
                        "https://www.jumbocolombia.com/supermercado/despensa",
                        "https://www.jumbocolombia.com/supermercado/lacteos-huevos-y-refrigerados",
                        "https://www.jumbocolombia.com/supermercado/frutas-y-verduras",
                        "https://www.jumbocolombia.com/supermercado/pescados-y-mariscos",
                        "https://www.jumbocolombia.com/supermercado/carne-y-pollo",
                        "https://www.jumbocolombia.com/supermercado/panaderia-y-pasteleria",
                        "https://www.jumbocolombia.com/supermercado/dulces-y-postres",
                        "https://www.jumbocolombia.com/supermercado/pasabocas",
                        "https://www.jumbocolombia.com/supermercado/charcuteria",
                        "https://www.jumbocolombia.com/supermercado/vinos-y-licores"
                          ]

START_URLS_SUPERMARKET_2 = [
                          "https://www.jumbocolombia.com/supermercado/bebidas",
                          "https://www.jumbocolombia.com/supermercado/aseo-de-hogar",
                          "https://www.jumbocolombia.com/supermercado/cuidado-personal",
                          "https://www.jumbocolombia.com/supermercado/belleza",
                          "https://www.jumbocolombia.com/supermercado/cuidado-de-ropa-y-calzado",
                          "https://www.jumbocolombia.com/supermercado/limpieza-de-cocina",
                          "https://www.jumbocolombia.com/supermercado/platos-preparados",
                          "https://www.jumbocolombia.com/supermercado/cuidado-del-bebe",
                          "https://www.jumbocolombia.com/supermercado/bolsas",
                          "https://www.jumbocolombia.com/supermercado/cigarrillos-y-tabacos"
]

XPATH_HOVER_MAIN_CATEGORY_SUPERMERCADO = "//a[@href='/supermercado' and contains(@class,'jumbo-main-menu-2-x-link--header-submenu-item')]"

START_URLS_ELECTRO = ["https://www.jumbocolombia.com/tecnologia/informatica",
                      "https://www.jumbocolombia.com/tecnologia/consolas-y-videojuegos",
                      "https://www.jumbocolombia.com/tecnologia/impresion",
                      "https://www.jumbocolombia.com/tecnologia/accesorios-para-computador",
                      "https://www.jumbocolombia.com/tecnologia/camaras-y-drones",
                      "https://www.jumbocolombia.com/tecnologia/smart-home",
                      "https://www.jumbocolombia.com/electrodomesticos/refrigeracion",
                      "https://www.jumbocolombia.com/electrodomesticos/lavadoras-y-secadoras",
                      "https://www.jumbocolombia.com/electrodomesticos/climatizacion",
                      "https://www.jumbocolombia.com/electrodomesticos/pequenos-electrodomesticos",
                      "https://www.jumbocolombia.com/electrodomesticos/cocina",
                      "https://www.jumbocolombia.com/electrodomesticos/cuidado-personal",
                      ]

XPATH_HOVER_MAIN_CATEGORY_TECNOLOGIA = "//a[@href='/tecnologia' and contains(@class,'jumbo-main-menu-2-x-link--header-submenu-item')]"
XPATH_HOVER_MAIN_CATEGORY_ELECTRODOMESICOS = "//a[@href='/electrodomesticos' and contains(@class,'jumbo-main-menu-2-x-link--header-submenu-item')]"

REGULAR_EXPRESSION_UNITS_SIMPLE = r'(?:x|por)\s*(\d+[\.,]?\d*)\b'

XPATH_HOVER_MAIN_CATEGORY_SALUD = "//a[@href='/salud-y-bienestar' and contains(@class,'jumbo-main-menu-2-x-link--header-submenu-item')]"

ID = '900.155.107'
NAME = 'Jumbo'

XPATH_GET_ALL_PRODUCTS = "//div[@id='gallery-layout-container']//article[contains(@class, 'vtex-product-summary-2-x-element')]/div"
XPATH_GET_PRICE = ".//div[contains(@class, 'selling-price')]//text()"
XPATH_GET_BREADCRUMBS = "//div[@data-testid = 'breadcrumb']/span/a//text()"
XPATH_CLICK_BUTTON = "//li[button/@id='active']/following-sibling::li[1]/button"
XPATH_UNIT_PRICE = ".//div[contains(@class, 'calculate-pum-2-x-main')]"
XPATH_TOTAL_COUNT_PRODUCTS = "//div[contains(@class, '-totalProducts--layout')]/span/text()"
XPATH_CATEGORY_SUB_CATEGORY = "//li[contains(@class, 'tiendasjumboqaio-jumbo-main-menu-2-x-second_li--header-submenu-item')]"
XPATH_A_SUB_CATEGORY = "//a[contains(@class, 'item_node_inner_third_level--header-submenu-item')]"
XPATH_BUTTON_GET_CATEGORIES = "//button[contains(@class, 'triggerButton--tigger-dropdown-mega-menu')]"

SELECTOR_CONTAINER_PRODUCTS = "#gallery-layout-container"

SELECTOR_LOAD_PRODUCTS = "#gallery-layout-container > div > section > a > article > div"
SELECTOR_CLICK_BUTTON = "button#noActive"
SELECTOR_BREADCRUMBS = "div[data-testid='breadcrumb'] > span > a"
SELECTOR_PRODUCT_CARDS = "div#gallery-layout-container article.vtex-product-summary-2-x-element > div"
SELECTOR_TOTAL_COUNT_PRODUCTS = "div[class*='totalProducts--layout'] > span"

SELECTOR_OLDER_AGE= "button[class='tiendasjumboqaio-delivery-modal-3-x-ofAgebutton']"
