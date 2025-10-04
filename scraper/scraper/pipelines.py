# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from scraper.items import ScraperItem
from scraper.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


class PostgresPipeline:

    def __init__(self):
        hostname = DB_HOST
        username = DB_USER
        password = DB_PASSWORD
        database = DB_NAME

        self.connection = psycopg2.connect(
            host=hostname,
            user=username,
            password=password,
            dbname=database,
        )

        self.cur = self.connection.cursor()
        self.cur.execute("SET search_path TO db_scrapy, public;")

    def open_spider(self, spider):
        spider.logger.info("Pipeline de PostgreSQL iniciado.")

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()
        spider.logger.info("Pipeline de PostgreSQL cerrado.")

    def process_item(self, item, spider):
        if isinstance(item, ScraperItem):
            adapter = ItemAdapter(item)
            try:
                insert_sql = """
                    INSERT INTO colombia (
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

            except Exception as e:
                self.connection.rollback()
                spider.logger.error(
                    f"Error al guardar el item en PostgreSQL: {e}")

        return item
