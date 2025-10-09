"""
Pipeline compartido para proyectos de scraping de supermercados
Este pipeline se adapta automáticamente según el proyecto que lo use
"""

from itemadapter import ItemAdapter
import psycopg2
import os
import dotenv


class UnifiedPostgresPipeline:
    """
    Pipeline unificado que recibe configuración específica como parámetros
    """

    def __init__(self, table_name='colombia', comercial_name='Jumbo', comercial_id='jumbo_colombia'):
        """
        Inicializar con parámetros específicos del proyecto
        """
        # Configuración específica del proyecto
        self.table_name = table_name
        self.comercial_name = comercial_name
        self.comercial_id = comercial_id
        
        # Cargar variables de entorno
        current_path = os.getcwd()
        
        # Buscar el archivo .env en el directorio raíz del proyecto
        if 'scraper_vea' in current_path:
            env_path = os.path.join(os.path.dirname(current_path), '.env')
        else:
            env_path = os.path.join(os.path.dirname(current_path), '.env')
        
        # Si estamos en el directorio interno del proyecto, subir un nivel más
        if not os.path.exists(env_path):
            env_path = os.path.join(os.path.dirname(os.path.dirname(current_path)), '.env')
        
        dotenv.load_dotenv(env_path)
        
        # Cargar variables de base de datos desde .env
        self.hostname = os.getenv('db_hostname')
        self.username = os.getenv('db_username')
        self.password = os.getenv('db_password')
        self.database = os.getenv('db_name')
        self.port = os.getenv('db_port', '11514')  

    @classmethod
    def from_crawler(cls, crawler):
        """Crear instancia desde crawler con configuración personalizada"""
        return cls(
            table_name=crawler.settings.get('PIPELINE_TABLE_NAME', 'colombia'),
            comercial_name=crawler.settings.get('PIPELINE_COMERCIAL_NAME', 'Jumbo'),
            comercial_id=crawler.settings.get('PIPELINE_COMERCIAL_ID', 'jumbo_colombia')
        )

    def open_spider(self, spider):
        """Conectar a PostgreSQL cuando inicia el spider"""
        try:
            self.connection = psycopg2.connect(
                host=self.hostname,
                user=self.username,
                password=self.password,
                database=self.database,
                port=self.port,
                sslmode='verify-ca',
                sslrootcert='./ca.pem'
            )
            self.cur = self.connection.cursor()
            
            # Establecer el schema
            self.cur.execute("SET search_path TO db_scrapy, public;")
            
            spider.logger.info(f"Pipeline PostgreSQL iniciado - Tabla: {self.table_name}")
            spider.logger.info(f"Conectado a: {self.hostname}:{self.port}/{self.database}")
            
        except Exception as e:
            spider.logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    def close_spider(self, spider):
        """Cerrar conexión cuando termina el spider"""
        try:
            self.cur.close()
            self.connection.close()
            spider.logger.info("Pipeline PostgreSQL cerrado.")
        except Exception as e:
            spider.logger.error(f"Error cerrando conexión PostgreSQL: {e}")

    def process_item(self, item, spider):
        """Procesar y guardar item en la base de datos"""
        # Procesar cualquier item que tenga los atributos necesarios
        adapter = ItemAdapter(item)
        
        try:
            # SQL dinámico usando el nombre de tabla de la configuración
            insert_sql = f"""
                INSERT INTO {self.table_name} (
                    name, price, unit_price, total_unit_quantity, unit_type,
                    category, sub_category, comercial_name, comercial_id,
                    result_date, result_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

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

            self.connection.commit()
            spider.logger.info(f"Item guardado en tabla {self.table_name}: {adapter.get('name')}")

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"Error guardando item en PostgreSQL: {e}")
            raise

        return item


# Mantener el nombre original para compatibilidad
PostgresPipeline = UnifiedPostgresPipeline