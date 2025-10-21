# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from scraper.items import ScraperItem
from scraper.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from scrapy.exceptions import NotConfigured


class PostgresPipeline:

    def __init__(self):
        self.pais = None

    def _connect(self):
        """Establecer conexión a la base de datos"""
        hostname = DB_HOST
        username = DB_USER
        password = DB_PASSWORD
        database = DB_NAME
        port = DB_PORT

        self.connection = psycopg2.connect(
            host=hostname,
            user=username,
            password=password,
            dbname=database,
            port=port
        )

        self.cur = self.connection.cursor()
        self.cur.execute("SET search_path TO public;")
        print(
            f"Conexión a PostgreSQL establecida para la tabla '{self.pais}'.")
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

    def open_spider(self, spider):
        """
        Se llama cuando la araña se abre. Aquí leemos el país
        y establecemos la conexión.
        """
        # --- ¡CLAVE AQUÍ! Leemos el atributo 'pais' de la araña ---
        self.pais = getattr(spider, 'pais', None)
        if not self.pais:
            spider.logger.error(
                "¡ERROR! La araña no tiene definido el atributo 'pais'. No se puede conectar a la BD.")
            # Puedes lanzar una excepción si quieres detener el scraper
            # raise scrapy.exceptions.NotConfigured("Spider attribute 'pais' is required for PostgresPipeline")
        else:
            spider.logger.info(
                f"Pipeline de PostgreSQL iniciando para la tabla '{self.pais}'...")
            self._connect()  # Nos conectamos usando el país obtenido

    def close_spider(self, spider):
        if self.cur:
            self.cur.close()
        if self.connection:
            self.connection.close()
        spider.logger.info(
            f"Pipeline de PostgreSQL cerrado para la tabla '{self.pais}'.")

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
        if not self.connection or self.connection.closed != 0 or not self.cur:
            spider.logger.error(
                f"No hay conexión a BD válida para tabla '{self.pais}'. Descartando item: {item.get('name')}")
            return item  # O raise DropItem

        self._reconnect_if_needed(spider)

        # Volver a verificar después del intento de reconexión
        if not self.connection or self.connection.closed != 0 or not self.cur:
            spider.logger.error(
                f"Reconexión fallida para tabla '{self.pais}'. Descartando item: {item.get('name')}")
            return item  # O raise DropItem
        if isinstance(item, ScraperItem):
            adapter = ItemAdapter(item)

            try:
                insert_sql = f"""
                    INSERT INTO {self.pais} (
                        name, price, unit_price, total_unit_quantity, unit_type,
                        category, sub_category, comercial_name, comercial_id,
                        result_date, result_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    adapter.get('result_date'),
                    adapter.get('result_time')
                )

                # spider.logger.info(
                #     f"Insertando producto en tabla '{self.pais}': {adapter.get('name')} - {adapter.get('comercial_name')}")
                # spider.logger.debug(f"Datos a insertar: {data_tuple}")

                self.cur.execute(insert_sql, data_tuple)
                self.connection.commit()

                # spider.logger.info(
                #     f"Producto guardado exitosamente en la tabla '{self.pais}'")

            except Exception as e:
                try:
                    if hasattr(self, 'connection') and self.connection and self.connection.closed == 0:
                        self.connection.rollback()
                except Exception as rollback_error:
                    spider.logger.warning(
                        f"Error en rollback: {rollback_error}")

                # spider.logger.error(
                #     f"Error al guardar el item en PostgreSQL tabla '{self.pais}': {e}")
                # spider.logger.error(f"Datos del item: {dict(adapter)}")

        return item
