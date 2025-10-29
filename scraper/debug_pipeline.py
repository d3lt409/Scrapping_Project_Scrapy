#!/usr/bin/env python3
"""
Script de debug para identificar problemas en el pipeline
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Probar las importaciones"""
    try:
        print("1. Probando importación de scrapy...")
        import scrapy
        print(f"   ✓ Scrapy {scrapy.__version__} importado correctamente")
        
        print("2. Probando importación de items...")
        from scraper.items import JuriscolItem
        print("   ✓ JuriscolItem importado correctamente")
        
        print("3. Probando creación de item...")
        item = JuriscolItem()
        item['tipo'] = 'Test'
        item['numero'] = '123'
        item['ano'] = 2025
        print(f"   ✓ Item creado: {item['result_datetime']}")
        
        print("4. Probando importación de config...")
        from scraper.config import DB_HOST, DB_PORT
        print(f"   ✓ Config importado: DB_HOST={DB_HOST}, DB_PORT={DB_PORT}")
        
        print("5. Probando importación de pipeline...")
        from scraper.pipelines import JuriscolPipeline
        print("   ✓ JuriscolPipeline importado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error general: {e}")
        return False

def test_database_connection():
    """Probar conexión a base de datos"""
    try:
        print("\n6. Probando conexión a base de datos...")
        import psycopg2
        from scraper.config import DB_HOST, DB_PORT, DB_SSL_PATH, DB_USER, DB_PASSWORD, DB_NAME
        
        connection = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            port=DB_PORT,
            sslmode='verify-ca',
            sslrootcert=DB_SSL_PATH
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✓ Conexión exitosa: {version}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error de conexión DB: {e}")
        return False

def test_pipeline_creation():
    """Probar creación del pipeline"""
    try:
        print("\n7. Probando creación de pipeline...")
        from scraper.pipelines import JuriscolPipeline
        
        # Intentar crear el pipeline
        pipeline = JuriscolPipeline()
        print("   ✓ Pipeline creado exitosamente")
        
        # Cerrar conexiones
        if hasattr(pipeline, 'cur') and pipeline.cur:
            pipeline.cur.close()
        if hasattr(pipeline, 'connection') and pipeline.connection:
            pipeline.connection.close()
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== DEBUG DEL PIPELINE JURISCOL ===\n")
    
    success = True
    success &= test_imports()
    success &= test_database_connection()
    success &= test_pipeline_creation()
    
    print(f"\n=== RESULTADO: {'✓ TODOS LOS TESTS PASARON' if success else '❌ ALGUNOS TESTS FALLARON'} ===")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())