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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_datetime = datetime.datetime.now()
        self['result_datetime'] = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

