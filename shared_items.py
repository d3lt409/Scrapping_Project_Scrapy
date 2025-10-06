# Items compartidos para proyectos de scraping de supermercados
#
# Define los modelos de datos unificados que se adaptan automáticamente
# según el proyecto que los use

import datetime
import scrapy
import os


class SharedSupermercadoItem(scrapy.Item):
    """Item base compartido para todos los supermercados"""
    
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
        
        # Establecer fecha y hora automáticamente
        current_date = datetime.datetime.now()
        self['result_date'] = current_date.strftime('%Y-%m-%d')
        self['result_time'] = current_date.strftime('%H:%M:%S')
        
        # Detectar proyecto y establecer valores por defecto
        current_path = os.getcwd()
        
        if 'scraper_vea' in current_path:
            # Configuración para PlazaVea
            self['comercial_name'] = 'PlazaVea'
            self['comercial_id'] = '20608300393'
        else:
            # Configuración para Jumbo (por defecto)
            self['comercial_name'] = 'Jumbo'
            self['comercial_id'] = 'jumbo_colombia'


# Aliases para compatibilidad con nombres específicos de proyectos
ScraperItem = SharedSupermercadoItem
ScraperVeaItem = SharedSupermercadoItem

# Item genérico que se puede usar directamente
SupermercadoItem = SharedSupermercadoItem