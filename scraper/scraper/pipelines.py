# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from scraper.items import ScraperItem, JuriscolItem
from scraper.config import (
    DB_HOST,
    DB_PORT,
    DB_SSL_PATH,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_SSL_MODE,
)


class JuriscolPipeline:
    """Pipeline específico para items de Juriscol"""
    
    def __init__(self):
        self._connect()
        self.items_processed = 0
        self.items_duplicated = 0
        self.items_inserted = 0

    def _connect(self):
        """Establecer conexión a la base de datos"""
        hostname = DB_HOST
        username = DB_USER
        password = DB_PASSWORD
        database = DB_NAME
        port = DB_PORT

        # Preparar argumentos SSL según configuración
        ssl_args = {}
        if DB_SSL_MODE:
            ssl_args['sslmode'] = DB_SSL_MODE
        # Solo incluir sslrootcert si el modo requiere verificación
        if DB_SSL_MODE in ('verify-ca', 'verify-full') and DB_SSL_PATH:
            ssl_args['sslrootcert'] = DB_SSL_PATH

        self.connection = psycopg2.connect(
            host=hostname,
            user=username,
            password=password,
            dbname=database,
            port=port,
            **ssl_args
        )

        self.cur = self.connection.cursor()
        self.cur.execute("SET search_path TO public;")
        
        # Crear tabla si no existe
        self.create_table_if_not_exists()
        
    def create_table_if_not_exists(self):
        """Crear la tabla de legislacion_col si no existe"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS legislacion_col (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(50) NOT NULL,
            numero VARCHAR(20) NOT NULL,
            ano INTEGER NOT NULL,
            sector VARCHAR(200) NOT NULL,
            emisor VARCHAR(500) NOT NULL,
            estado VARCHAR(100),
            epigrafe TEXT,
            documento_url VARCHAR(1000),
            result_datetime TIMESTAMP NOT NULL,

            CONSTRAINT uk_legislacion_col_documento UNIQUE (tipo, numero, ano, sector)
        );
        """
        
        try:
            self.cur.execute(create_table_sql)
            self.connection.commit()
        except Exception as e:
            print(f"Error creando tabla legislacion_col: {e}")
            self.connection.rollback()

    def open_spider(self, spider):
        spider.logger.info("Pipeline de Juriscol iniciado.")

    def close_spider(self, spider):
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
            
        spider.logger.info(f"Pipeline de Juriscol cerrado. Estadísticas:")
        spider.logger.info(f"  - Items procesados: {self.items_processed}")
        spider.logger.info(f"  - Items insertados: {self.items_inserted}")
        spider.logger.info(f"  - Items duplicados: {self.items_duplicated}")

    def process_item(self, item, spider):
        if isinstance(item, JuriscolItem):
            adapter = ItemAdapter(item)
            self.items_processed += 1
            
            try:
                insert_sql = """
                    INSERT INTO legislacion_col (
                        tipo, numero, ano, sector, emisor, estado, epigrafe, documento_url,
                        result_datetime
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    -- ON CONFLICT (tipo, numero, ano, sector) DO NOTHING;
                """
                
                data_tuple = (
                    adapter.get('tipo'),
                    adapter.get('numero'),
                    adapter.get('ano'),
                    adapter.get('sector'),
                    adapter.get('emisor'),
                    adapter.get('estado'),
                    adapter.get('epigrafe'),
                    adapter.get('documento_url'),
                    adapter.get('result_datetime')
                )
                
                # Ejecutar inserción
                self.cur.execute(insert_sql, data_tuple)
                
                # Verificar si se insertó (rowcount > 0 significa inserción exitosa)
                if self.cur.rowcount > 0:
                    self.items_inserted += 1
                    spider.logger.info(f"Documento insertado: {adapter.get('tipo')} {adapter.get('numero')}/{adapter.get('ano')}")
                else:
                    self.items_duplicated += 1
                    spider.logger.debug(f"Documento duplicado ignorado: {adapter.get('tipo')} {adapter.get('numero')}/{adapter.get('ano')}")
                
                self.connection.commit()

            except Exception as e:
                try:
                    if hasattr(self, 'connection') and self.connection and self.connection.closed == 0:
                        self.connection.rollback()
                except Exception as rollback_error:
                    spider.logger.warning(f"Error en rollback: {rollback_error}")
                    
                spider.logger.error(f"Error al guardar el item de Juriscol: {e}")
                spider.logger.error(f"Datos del item: {dict(adapter)}")

        return item


class PostgresPipeline:

    def __init__(self, pais='peru'):
        self.pais = pais
        self._connect()

    def _connect(self):
        """Establecer conexión a la base de datos"""
        hostname = DB_HOST
        username = DB_USER
        password = DB_PASSWORD
        database = DB_NAME
        port = DB_PORT

        # Preparar argumentos SSL según configuración
        ssl_args = {}
        if DB_SSL_MODE:
            ssl_args['sslmode'] = DB_SSL_MODE
        if DB_SSL_MODE in ('verify-ca', 'verify-full') and DB_SSL_PATH:
            ssl_args['sslrootcert'] = DB_SSL_PATH

        self.connection = psycopg2.connect(
            host=hostname,
            user=username,
            password=password,
            dbname=database,
            port=port,
            **ssl_args
        )

        self.cur = self.connection.cursor()
        self.cur.execute("SET search_path TO public;")
        
        # Verificar el esquema actual
        self.cur.execute("SELECT current_schema();")
        current_schema = self.cur.fetchone()[0]
        print(f"Esquema actual: {current_schema}")
        
        # Verificar si la tabla existe
        self.cur.execute(f"""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name = '{self.pais}'
        """)
        tables = self.cur.fetchall()
        print(f"Tablas '{self.pais}' encontradas: {tables}")

    @classmethod
    def from_crawler(cls, crawler):
        # Obtener el país desde settings, por defecto 'peru'
        pais = crawler.settings.get('DATABASE_COUNTRY', 'peru')
        return cls(pais=pais)

    def open_spider(self, spider):
        spider.logger.info("Pipeline de PostgreSQL iniciado.")

    def close_spider(self, spider):
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
        spider.logger.info("Pipeline de PostgreSQL cerrado.")

    def _reconnect_if_needed(self, spider):
        """Reconectar si la conexión está cerrada"""
        try:
            # Probar la conexión
            if self.connection.closed != 0:
                raise psycopg2.InterfaceError("Connection is closed")
            self.cur.execute("SELECT 1;")
        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            spider.logger.warning(f"Conexión perdida, reconectando: {e}")
            try:
                # Cerrar conexiones existentes si están abiertas
                if hasattr(self, 'cur') and self.cur:
                    self.cur.close()
                if hasattr(self, 'connection') and self.connection:
                    self.connection.close()
            except:
                pass
            
            # Reestablecer conexión
            self._connect()
            spider.logger.info("Reconexión a PostgreSQL exitosa")

    def process_item(self, item, spider):
        if isinstance(item, ScraperItem):
            adapter = ItemAdapter(item)
            
            # Verificar y reconectar si es necesario
            self._reconnect_if_needed(spider)
            
            try:
                insert_sql = f"""
                    INSERT INTO {self.pais} (
                        name, price, unit_price, total_unit_quantity, unit_type,
                        category, sub_category, comercial_name, comercial_id,
                        result_datetime
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                data_tuple = (
                    adapter.get('name'),
                    adapter.get('price'),
                    adapter.get('unit_price'),
                    adapter.get('total_unit_quantity'),
                    adapter.get('unit_type'),
                    adapter.get('category'),
                    adapter.get('sub_category'),
                    adapter.get('comercial_name'),
                    adapter.get('comercial_id'),
                    adapter.get('result_datetime')
                )
                
                spider.logger.info(f"Insertando producto en tabla '{self.pais}': {adapter.get('name')} - {adapter.get('comercial_name')}")
                spider.logger.debug(f"Datos a insertar: {data_tuple}")
                
                self.cur.execute(insert_sql, data_tuple)
                self.connection.commit()
                
                spider.logger.info(f"Producto guardado exitosamente en la tabla '{self.pais}'")

            except Exception as e:
                try:
                    if hasattr(self, 'connection') and self.connection and self.connection.closed == 0:
                        self.connection.rollback()
                except Exception as rollback_error:
                    spider.logger.warning(f"Error en rollback: {rollback_error}")
                    
                spider.logger.error(f"Error al guardar el item en PostgreSQL tabla '{self.pais}': {e}")
                spider.logger.error(f"Datos del item: {dict(adapter)}")

        return item
