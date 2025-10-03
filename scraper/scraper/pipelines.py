# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from scraper.items import ScraperItem


class PostgresPipeline:
    
    def __init__(self):
        # --- CONFIGURA AQUÍ TUS CREDENCIALES ---
        hostname = 'localhost'
        username = 'd3lt409' # O tu usuario de Postgres
        password = 'manuelfer' # Tu contraseña de Postgres
        database = 'db_scraper' # El nombre de la base de datos que creaste
        
        # Se establece la conexión
        self.connection = psycopg2.connect(
            host=hostname, 
            user=username, 
            password=password, 
            dbname=database
        )
        
        # Se crea un cursor para ejecutar las sentencias SQL
        self.cur = self.connection.cursor()
        
    def open_spider(self, spider):
        spider.logger.info("Pipeline de PostgreSQL iniciado.")

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()
        spider.logger.info("Pipeline de PostgreSQL cerrado.")
        
    def process_item(self, item, spider):
        # Nos aseguramos de que el item sea del tipo que esperamos
        if isinstance(item, ScraperItem):
            adapter = ItemAdapter(item)
            try:
                # Definimos la sentencia SQL para insertar los datos
                # Usamos %s para prevenir inyección SQL
                insert_sql = """
                    INSERT INTO colombia (
                        name, price, unit_price, total_unit_quantity, unit_type,
                        category, sub_category, comercial_name, comercial_id,
                        result_date, result_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Ejecutamos la sentencia con los datos del item
                self.cur.execute(insert_sql, (
                    adapter.get('name'),
                    adapter.get('price'),
                    adapter.get('unit_price'),
                    adapter.get('total_unit_quantity'),
                    adapter.get('unit_type'),
                    adapter.get('category'),
                    adapter.get('sub_category'),
                    adapter.get('comercial_name'),
                    adapter.get('comercial_id'),
                    adapter.get('result_date'),
                    adapter.get('result_time')
                ))
                
                # Confirmamos la transacción
                self.connection.commit()
                
            except Exception as e:
                # Si hay un error, lo deshacemos para no dejar datos corruptos
                self.connection.rollback()
                spider.logger.error(f"Error al guardar el item en PostgreSQL: {e}")
        
        # Es obligatorio devolver el item para que otros pipelines (si los hay) lo puedan procesar
        return item
