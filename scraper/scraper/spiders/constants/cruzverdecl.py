
NAME = "Cruz Verde CL"
ID = "89.807.200"

SELECTOR_BUTTON_LOCATION = "at-button > button[class='btn md:my-0 w-full bg-prices hover:bg-prices h-full px-10 btn-secondary']"
SELECTOR_BUTTON_OFFERS = "#onesignal-slidedown-cancel-button"
SELECTOR_BUTTON_CATEGORIES = "div[class='flex items-center cursor-pointer']"
SELECTOR_GET_ALL_CATEGORIES = "div[class*='flex-1 hover:bg-main hover:text-white option text-gray-darkest ng-star-inserted'] > h4"
SELECTOR_CLICK_SUB_CATEGORIES = "li[class='ng-star-inserted'] > ml-accordion span[class='text-accent ng-star-inserted']"
SELECTOR_GET_ALL_SUB_CATEGORIES = "div[class='grid grid-cols-3 gap-x-30'] li[class='ng-star-inserted'] "
SELECTOR_GET_SUB_CATEGORIES_INSIDE = "at-link > a"
SELECTOR_GET_ALL_PRODUCTS = "ml-new-card-product div[class='text-left']"
SELECTOR_CONTAINER_PRODUCTS = "div[class=\"grid grid-cols-1 gap-15 lg:grid-cols-3 lg:gap-30 ng-star-inserted\"]"
SELECTOR_PRODUCT_NAME = SELECTOR_GET_ALL_PRODUCTS + " > h2 span"


XPATH_GET_PRICE = ".//ml-price-tag-v2//div/p/text()"
XPATH_GET_NAME = ".//h2//span/text()"
XPATH_CLICK_NEXT_PAGE = "//ml-pagination//div[contains(@class,'bg-main!')]/following-sibling::div[1]"
