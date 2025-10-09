#!/usr/bin/env python3
"""
Script para configurar automáticamente la base de datos scrapy_supermercado
Usa el mismo patrón del pipeline con variables de entorno
"""

import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DB_HOST = os.getenv('db_hostname')
DB_USER = os.getenv('db_username')
DB_PASSWORD = os.getenv('db_password')
DB_NAME = os.getenv('db_name')
DB_PORT = os.getenv('db_port', '11514') 


class DatabaseSetup:
    
    def __init__(self):
        hostname = DB_HOST
        username = DB_USER
        password = DB_PASSWORD
        database = DB_NAME
        
        # Primero crear la base de datos si no existe
        self._create_database_if_not_exists(hostname, username, password, database)
        
        # Luego conectar a la base de datos específica
        self.connection = psycopg2.connect(
            host=hostname,
            user=username,
            password=password,
            dbname=database,
            port=DB_PORT,
            sslmode='verify-ca',
            sslrootcert='./ca.pem'
        )
        
        self.connection.autocommit = True
        self.cur = self.connection.cursor()
        
        print(f"✅ Conectado a la base de datos: {database}")
    
    def _create_database_if_not_exists(self, hostname, username, password, database):
        """Crear la base de datos si no existe"""
        try:
            # Conectar a postgres para crear la BD
            temp_conn = psycopg2.connect(
                host=hostname,
                user=username,
                password=password,
                dbname=DB_NAME,
                port=DB_PORT,
                sslmode='require'
            )
            temp_conn.autocommit = True
            temp_cur = temp_conn.cursor()
            
            # Verificar si la BD existe
            temp_cur.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                (database,)
            )
            
            if not temp_cur.fetchone():
                temp_cur.execute(f'CREATE DATABASE "{database}"')
                print(f"Base de datos '{database}' creada")
            else:
                print(f"Base de datos '{database}' ya existe")
            
            temp_cur.close()
            temp_conn.close()
            
        except Exception as e:
            print(f"❌ Error creando base de datos: {e}")
            raise
    
    def setup_schema_and_tables(self):
        """Crear esquema y tablas"""
        try:
            # Crear esquema db_scrapy
            self.cur.execute("CREATE SCHEMA IF NOT EXISTS db_scrapy;")
            print("Esquema db_scrapy creado")
            
            # Configurar search_path
            self.cur.execute("SET search_path TO db_scrapy, public;")
            
            # Crear tabla peru
            create_peru_table = """
            CREATE TABLE IF NOT EXISTS db_scrapy.peru (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price VARCHAR(50),
                unit_price VARCHAR(50),
                total_unit_quantity VARCHAR(50),
                unit_type VARCHAR(50),
                category VARCHAR(255),
                sub_category VARCHAR(255),
                comercial_name VARCHAR(100) DEFAULT 'PlazaVea',
                comercial_id VARCHAR(50) DEFAULT 'plaza_vea',
                result_date DATE NOT NULL,
                result_time TIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            self.cur.execute(create_peru_table)
            print("✅ Tabla peru creada")
            
            # Crear tabla colombia (compatibilidad)
            create_colombia_table = """
            CREATE TABLE IF NOT EXISTS db_scrapy.colombia (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price VARCHAR(50),
                unit_price VARCHAR(50),
                total_unit_quantity VARCHAR(50),
                unit_type VARCHAR(50),
                category VARCHAR(255),
                sub_category VARCHAR(255),
                comercial_name VARCHAR(100),
                comercial_id VARCHAR(50),
                result_date DATE NOT NULL,
                result_time TIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            self.cur.execute(create_colombia_table)
            print("✅ Tabla colombia creada")
            
            # Crear índices para optimizar consultas
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_peru_comercial ON db_scrapy.peru(comercial_name, comercial_id);",
                "CREATE INDEX IF NOT EXISTS idx_peru_date ON db_scrapy.peru(result_date);",
                "CREATE INDEX IF NOT EXISTS idx_peru_category ON db_scrapy.peru(category);",
                "CREATE INDEX IF NOT EXISTS idx_peru_name ON db_scrapy.peru(name);",
                "CREATE INDEX IF NOT EXISTS idx_colombia_comercial ON db_scrapy.colombia(comercial_name, comercial_id);",
                "CREATE INDEX IF NOT EXISTS idx_colombia_date ON db_scrapy.colombia(result_date);",
                "CREATE INDEX IF NOT EXISTS idx_colombia_category ON db_scrapy.colombia(category);",
                "CREATE INDEX IF NOT EXISTS idx_colombia_name ON db_scrapy.colombia(name);"
            ]
            
            for index_sql in indices:
                self.cur.execute(index_sql)
            
            print("✅ Índices creados")
            
        except Exception as e:
            print(f"Error configurando esquema y tablas: {e}")
            raise
    
    def verify_setup(self):
        """Verificar que todo se configuró correctamente"""
        try:
            # Verificar tablas creadas
            self.cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'db_scrapy'
                ORDER BY table_name;
            """)
            
            tables = self.cur.fetchall()
            print("\nTablas en esquema db_scrapy:")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Contar registros en cada tabla
            for table in tables:
                table_name = table[0]
                self.cur.execute(f"SELECT COUNT(*) FROM db_scrapy.{table_name};")
                count = self.cur.fetchone()[0]
                print(f"Registros en {table_name}: {count}")
            
            return True
            
        except Exception as e:
            print(f"Error verificando configuración: {e}")
            return False
    
    def close(self):
        """Cerrar conexión"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'connection'):
            self.connection.close()
        print("🔒 Conexión cerrada")


def main():
    """Función principal para configurar la base de datos"""
    print("CONFIGURADOR DE BASE DE DATOS - scrapy_supermercado")
    print("=" * 60)
    
    try:
        # Inicializar configurador
        db_setup = DatabaseSetup()
        
        # Configurar esquema y tablas
        db_setup.setup_schema_and_tables()
        
        # Verificar configuración
        if db_setup.verify_setup():
            print("\n¡Base de datos configurada correctamente!")
            print("El scraper está listo para ejecutarse")
        else:
            print("\nHubo problemas en la verificación")
        
        # Cerrar conexión
        db_setup.close()
        
    except Exception as e:
        print(f"\nError general: {e}")
        print("\nVerifica las credenciales en el archivo .env")


if __name__ == "__main__":
    main()