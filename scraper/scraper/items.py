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
    result_datetime = scrapy.Field()

    price = scrapy.Field()
    unit_price = scrapy.Field()
    total_unit_quantity = scrapy.Field()
    unit_type = scrapy.Field()

    comercial_name = scrapy.Field()
    comercial_id = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_datetime = datetime.datetime.now()
        self['result_datetime'] = current_datetime.strftime('%Y-%m-%d %H:%M:%S')


class JuriscolItem(scrapy.Item):
    # Información básica del documento
    tipo = scrapy.Field()           # Tipo de norma (Decreto, Ley, Resolución)
    numero = scrapy.Field()         # Número del documento
    ano = scrapy.Field()            # Año de emisión
    sector = scrapy.Field()         # Sector emisor
    emisor = scrapy.Field()         # Entidad emisora
    estado = scrapy.Field()         # Estado del documento (Vigente, Derogado, etc.)
    epigrafe = scrapy.Field()       # Descripción/epígrafe del documento
    documento_url = scrapy.Field()  # URL del documento completo
    
    # Metadata de scraping
    result_datetime = scrapy.Field()  # Fecha y hora de scraping
    search_vigencia = scrapy.Field()  # Estado de vigencia por el que se buscó
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_datetime = datetime.datetime.now()
        self['result_datetime'] = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
