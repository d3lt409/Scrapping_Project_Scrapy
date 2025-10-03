START_URLS_SUPERMARKET = ["https://www.jumbocolombia.com/supermercado/despensa/",
                          "https://www.jumbocolombia.com/supermercado/lacteos-huevos-y-refrigerados",
                          "https://www.jumbocolombia.com/supermercado/frutas-y-verduras",
                          "https://www.jumbocolombia.com/supermercado/pescados-y-mariscos",
                          "https://www.jumbocolombia.com/supermercado/carne-y-pollo",
                          "https://www.jumbocolombia.com/supermercado/panaderia-y-pasteleria",
                          "https://www.jumbocolombia.com/supermercado/dulces-y-postres",
                          "https://www.jumbocolombia.com/supermercado/pasabocas",
                          "https://www.jumbocolombia.com/supermercado/charcuteria",
                          "https://www.jumbocolombia.com/supermercado/vinos-y-licores",
                          "https://www.jumbocolombia.com/supermercado/bebidas",
                          "https://www.jumbocolombia.com/supermercado/aseo-de-hogar",
                          "https://www.jumbocolombia.com/supermercado/cuidado-personal",
                          "https://www.jumbocolombia.com/supermercado/belleza",
                          "https://www.jumbocolombia.com/supermercado/cuidado-de-ropa-y-calzado",
                          "https://www.jumbocolombia.com/supermercado/limpieza-de-cocina",
                          "https://www.jumbocolombia.com/supermercado/platos-preparados",
                          "https://www.jumbocolombia.com/supermercado/cuidado-del-bebe",
                          "https://www.jumbocolombia.com/supermercado/bolsas",
                          "https://www.jumbocolombia.com/supermercado/cigarrillos-y-tabacos",
                          ]

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

START_URLS_PHARMACY = ["https://www.jumbocolombia.com/salud-y-bienestar/drogueria",
                       "https://www.jumbocolombia.com/salud-y-bienestar/equipos-de-cuidado-en-casa",
                       "https://www.jumbocolombia.com/salud-y-bienestar/ortopedia-y-fisioterapia"]

ID = '900.155.107'
NAME = 'Jumbo'

XPATH_GET_ALL_PRODUCTS = "//div[@id='gallery-layout-container']//article[contains(@class, 'vtex-product-summary-2-x-element')]/div"
XPATH_GET_PRICE = ".//div[contains(@class, 'selling-price')]//text()"
XPATH_GET_BREADCRUMBS = "//div[@data-testid = 'breadcrumb']/span/a//text()"
XPATH_CLICK_BUTTON = "//button[@class='tiendasjumboqaio-jumbo-fetch-more-paginator-0-x-arrowNext ml2']"
XPATH_UNIT_PRICE = ".//div[contains(@class, 'calculate-pum-2-x-main')]"

SELECTOR_LOAD_PRODUCTS = "#gallery-layout-container > div > section > a > article > div"