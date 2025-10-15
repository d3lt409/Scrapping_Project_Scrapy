# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import datetime
import scrapy

class ScraperItem(scrapy.Item):
    name = scrapy.Field()
    category = scrapy.Field()
    sub_category = scrapy.Field()
    result_date = scrapy.Field()
    result_time = scrapy.Field()

    price = scrapy.Field()
    unit_price = scrapy.Field()
    total_unit_quantity = scrapy.Field()
    unit_type = scrapy.Field()

    comercial_name = scrapy.Field()
    comercial_id = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_date = datetime.datetime.now()
        self['result_date'] = current_date.strftime('%Y-%m-%d')
        self['result_time'] = current_date.strftime('%H:%M:%S')
    
    
