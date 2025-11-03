import dotenv
import os
dotenv.load_dotenv()

from pathlib import Path

# Carga robusta del archivo .env ubicado en la raíz del proyecto "scraper/.env",
# independientemente del directorio de ejecución.
THIS_DIR = Path(__file__).resolve().parent  # scraper/scraper
PROJECT_ROOT = THIS_DIR.parent              # scraper/
ENV_PATH = PROJECT_ROOT / ".env"

# Si existe el .env en la raíz del proyecto, cárguelo explícitamente
dotenv.load_dotenv(dotenv_path=str(ENV_PATH))

# Usar variables de producción
DB_HOST = os.getenv('db_hostname_prod')
DB_USER = os.getenv('db_username_prod')
DB_PASSWORD = os.getenv('db_password_prod')
DB_NAME = os.getenv('db_name_prod')
DB_PORT = os.getenv('db_port_prod')
# Aceptar cualquiera de los dos nombres en .env por compatibilidad
DB_SSL_PATH = os.getenv('db_ssl_path') or os.getenv('db_path_ssl')

# Modo SSL configurable. Por defecto, usar 'require' (válido para AWS RDS).
# Si cuentas con el certificado de CA y quieres validación estricta,
# puedes establecer en .env: db_ssl_mode=verify-ca (o verify-full).
DB_SSL_MODE = os.getenv('db_ssl_mode', 'require')

# Validación mínima para ayudar a diagnosticar problemas de entorno
if not DB_HOST:
	# No imprimir secretos; solo pistas útiles.
	hint = f".env buscado en: {ENV_PATH} (exists={ENV_PATH.exists()})"
	raise RuntimeError(f"DB_HOST vacío: no se cargaron variables de entorno de producción. {hint}")