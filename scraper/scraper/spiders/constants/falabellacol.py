NAME = 'Falabella'
ID = '76.212.492'

LIST_CATEGORIES = ["Tecnología",
                   "Electrohogar", "Celulares y accesorios"]

# SELECTORS
SELECTOR_BUTTON_CATEGORIES = "button[id='testId-HamburgerBtn-toggle']"
SELECTOR_CATEGORIES = "div[class*='FirstLevelCategories-module_categoryTitle__'] "
SELECTOR_SUB_CATEGORIES = "ul[class*='SecondLevelCategories-module_secondLevelCategory__NVToy']"
SELECTOR_SUB_CATEGORY_NAME = "li[class*='SecondLevelCategories-module_secondLevelCategoryTitle__'] > a"
SELECTOR_SUB_CATEGORIES_LINKS = "li[class='SecondLevelCategories-module_thirdLevelCategory__0VfiO'] > a"
SELECTOR_CONTAINER_PRODUCTS = "div[id*=\"testId-searchResults-products\"]"
SELECTOR_LOAD_PRODUCTS = SELECTOR_CONTAINER_PRODUCTS + " div"
SELECTOR_PRODUCT_CARDS = SELECTOR_LOAD_PRODUCTS + ' > a'
SELECTOR_PRODUCT_NAME = "b[id*='testId-pod-displaySubTitle-']"


SELECTOR_PRODUCT_PROMO_PRICE = "div[id*='testId-pod-prices-'] li[data-event-price] span"

# XPATHS
XPATH_NEXT_PAGE_BUTTON = "//button[contains(@id,'testId-pagination-bottom-button') and contains(@class,'active')]/following::button[1]"
XPATH_CATEGORIES = "//div[contains(@class,'FirstLevelCategories-module_categoryTitle__')]"
XPATH_CATEGORY_NAME = "//div[contains(@class,'FirstLevelCategories-module_categoryTitle__')][text()='{category}']"
XPATH_PRODUCT_CARDS = "//div[contains(@id,'testId-searchResults-products')]/div/a"
XPATH_PRODUCT_NAME = ".//b[contains(@id,'testId-pod-displaySubTitle-')]//text()"
XPATH_PRODUCT_PRICE = ".//div[contains(@id,'testId-pod-prices-')]//li[@data-normal-price]//span/text()"
XPATH_PRODUCT_PRICE1 = ".//div[contains(@id,'testId-pod-prices-')]//li[@data-internet-price]//span[@id='']/text()"
XPATH_PTODUCT_PRICE2 = "//div[contains(@id,'testId-pod-prices-')]//li[@data-event-price]//span[@id='']/text()"
