ID = '800.149.695'
NAME = 'Cruz Verde'

SELECTOR_CITY_ACEPTAR = "button[id='Aceptar'][class*='bg-prices hover:bg-prices']"

LIST_CATEGORIES = ["Medicamentos","Dermocosméticos","Bebé y Maternidad","Cuidado Personal","Salud Sexual","Belleza","Bienestar y Nutrición"]

SELECTOR_CLICK_CATEGORIES = "#category-menu"
SELECTOR_GET_ALL_CATEGORIES = "//*[@id ='category-list']//span/span"
SELECTOR_SEARCH_SUBCATEGORY = "//li//a[@class='font-open flex items-center']"
SELECTOR_CONTAINER_PRODUCTS = "div[class='grid grid-cols-1 gap-15 lg:grid-cols-3 lg:gap-30 ng-star-inserted']"
SELECTOR_GET_ALL_PRODUCTS = "div[class='flex flex-col h-full p-10 bg-white rounded-sm font-open sm:p-10']"

XPATH_GET_NAME = ".//a[@class='font-open flex items-center text-main text-16 sm:text-18 leading-20 font-semibold ellipsis hover:text-accent']//text()"
# XPATH_GET_PRICE = ".//div[@class='text-12 sm:text-14 line-through order-3 ng-star-inserted']//text()"
XPATH_GET_PRICE = ".//span[@class='font-bold text-prices']//text()"
XPATH_GET_UNIT_PRICE = ".//span[@class='text-12']//text()"
XPATH_CLICK_NEXT_PAGE = "//div[@class='rounded-full bg-quaternary ml-15 lg:h-32 lg:w-32 h-25 w-25 flex items-center justify-center cursor-pointer hover:bg-prices text-white ng-star-inserted']//*[@id='chevron-right']"