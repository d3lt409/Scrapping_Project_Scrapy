#!/usr/bin/env python3
"""
Runner para el spider de InkaFarma
Ejecuta el scraping de productos de InkaFarma con diferentes categorías
"""

import subprocess
import sys
import os
from datetime import datetime

# Importar las categorías desde las constantes
try:
    from scraper.spiders.constants.inkafarma import CATEGORIAS, CATEGORIA_URL_TEMPLATE
except ImportError:
    # Fallback si no se puede importar
    CATEGORIAS = [
        "inka-packs",
        "farmacia", 
        "salud",
        "mama-y-bebe",
        "nutricion-para-todos",
        "dermatologia-cosmetica",
        "cuidado-personal",
        "belleza",
        "limpieza-y-cuidado-para-el-hogar",
        "cuidado-del-cabello-1",
        "adulto-mayor-1",
        "dispositivos-medicos",
        "productos-naturales-1"
    ]
    CATEGORIA_URL_TEMPLATE = "https://inkafarma.pe/categoria/{categoria}"

def run_inkafarma_spider(categoria="farmacia", limit_items=None, custom_url=None):
    """
    Ejecuta el spider de InkaFarma
    
    Args:
        categoria (str): Categoría a scrapear (farmacia, belleza, etc.)
        limit_items (int): Límite de productos a extraer (None para todos)
        custom_url (str): URL personalizada (opcional)
    """
    print(f"Iniciando spider InkaFarma...")
    print(f"Categoria: {categoria}")
    print(f"Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Obtener rutas correctas
    current_dir = os.getcwd()
    project_root = os.path.dirname(current_dir)  # Directorio padre (Scrapping_Project_Scrapy)
    venv_path = os.path.join(project_root, "venv", "Scripts", "Activate.ps1")
    scrapy_dir = os.path.join(current_dir, "scraper")  # subdirectorio scraper donde está scrapy.cfg
    
    # Verificar que el directorio scrapy existe
    if not os.path.exists(scrapy_dir):
        print(f"Error: No se encuentra el directorio {scrapy_dir}")
        return
    
    # Construir comando PowerShell que active el venv y ejecute scrapy
    if custom_url:
        scrapy_cmd = f"scrapy crawl inkafarma -a custom_urls={custom_url}"
    else:
        # Usar la categoría para construir la URL
        url = f"https://inkafarma.pe/categoria/{categoria}"
        scrapy_cmd = f"scrapy crawl inkafarma -a custom_urls={url}"
    
    # Agregar límite de items si se especifica
    if limit_items:
        scrapy_cmd += f" -s CLOSESPIDER_ITEMCOUNT={limit_items}"
    
    # Comando completo que activa el venv, cambia de directorio y ejecuta scrapy
    full_cmd = f'& "{venv_path}"; cd "{scrapy_dir}"; {scrapy_cmd}'
    
    print(f"Comando a ejecutar: {scrapy_cmd}")
    print(f"Directorio de trabajo: {scrapy_dir}")
    print("="*60)
    
    try:
        # Ejecutar el comando usando PowerShell
        result = subprocess.run(
            ["powershell", "-Command", full_cmd], 
            capture_output=False, 
            text=True,
            cwd=scrapy_dir
        )
        
        print("="*60)
        if result.returncode == 0:
            print("Spider ejecutado exitosamente!")
        else:
            print(f"Error en la ejecución del spider. Código de salida: {result.returncode}")
            
        print(f"Hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error al ejecutar el spider: {e}")

def main():
    """Función principal con menú de categorías"""
    print("="*60)
    print("RUNNER SPIDER INKAFARMA")
    print("="*60)
    
    while True:
        print("\nCategorias disponibles:")
        
        # Mostrar todas las categorías numeradas
        for i, categoria in enumerate(CATEGORIAS, 1):
            categoria_display = categoria.replace("-", " ").title()
            print(f"{i:2d}. {categoria_display}")
        
        print(f"{len(CATEGORIAS)+1:2d}. Salir")
        
        try:
            opcion = int(input(f"\nSelecciona una categoria (1-{len(CATEGORIAS)+1}): ").strip())
            
            if 1 <= opcion <= len(CATEGORIAS):
                categoria_seleccionada = CATEGORIAS[opcion-1]
                categoria_display = categoria_seleccionada.replace("-", " ").title()
                print(f"\nEjecutando scraping de '{categoria_display}'...")
                run_inkafarma_spider(categoria=categoria_seleccionada)
                
            elif opcion == len(CATEGORIAS)+1:
                print("\nHasta luego!")
                break
                
            else:
                print("Opcion invalida, intenta de nuevo")
                
        except ValueError:
            print("Por favor ingresa un numero valido")

if __name__ == "__main__":
    main()