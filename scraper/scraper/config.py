import dotenv
import os
dotenv.load_dotenv()

DB_HOST = os.getenv('db_hostname')
DB_USER = os.getenv('db_username')
DB_PASSWORD = os.getenv('db_password')
DB_NAME = os.getenv('db_name')
