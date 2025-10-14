#!/usr/bin/env python3
"""
PlazaVea Scraper Runner - Adaptado al proyecto scraper principal
"""

import os
import sys
import asyncio

# Agregar el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_categories_from_constants():
    """Obtener categorías desde las constantes de PlazaVea del proyecto scraper"""
    try:
        from scraper.spiders.constants.plaza_vea import CATEGORIAS_MERCADO
        
        categories = {}
        
        for categoria, subcategorias in CATEGORIAS_MERCADO.items():
            display_name = categoria.replace('_', ' ').replace('-', ' ').title()
            categories[categoria] = {
                'display_name': display_name,
                'subcategorias': subcategorias,
                'urls': []
            }
            
            for subcategoria in subcategorias:
                url = f"https://www.plazavea.com.pe/{categoria}/{subcategoria}"
                categories[categoria]['urls'].append({
                    'url': url,
                    'subcategoria': subcategoria,
                    'display_name': subcategoria.replace('-', ' ').title()
                })
        
        return categories
    except ImportError as e:
        print(f"❌ Error importando constantes: {e}")
        print("💡 Usando categorías básicas como fallback...")
        
        # Fallback: categorías básicas si falla la importación
        categorias_fallback = {
            "frutas-y-verduras": ["frutas", "verduras"],
            "carnes-aves-y-pescados": ["pollo", "res", "cerdo", "pescados-y-mariscos"],
            "lacteos-y-huevos": ["leche", "yogurt", "huevos"],
            "abarrotes": ["arroz", "aceite", "fideos-pastas-y-salsas"],
            "bebidas": ["gaseosas", "aguas", "jugos-y-otras-bebidas"]
        }
        
        categories = {}
        for categoria, subcategorias in categorias_fallback.items():
            display_name = categoria.replace('_', ' ').replace('-', ' ').title()
            categories[categoria] = {
                'display_name': display_name,
                'subcategorias': subcategorias,
                'urls': []
            }
            
            for subcategoria in subcategorias:
                url = f"https://www.plazavea.com.pe/{categoria}/{subcategoria}"
                categories[categoria]['urls'].append({
                    'url': url,
                    'subcategoria': subcategoria,
                    'display_name': subcategoria.replace('-', ' ').title()
                })
        
        return categories

def show_categories(categories):
    """Mostrar categorías disponibles"""
    print("📋 CATEGORÍAS DISPONIBLES:")
    print("=" * 60)
    
    for i, (key, data) in enumerate(categories.items(), 1):
        subcategory_count = len(data['subcategorias'])
        print(f"{i:2d}. {data['display_name']} ({subcategory_count} subcategorías)")
    
    print(f"\n📊 Total: {len(categories)} categorías principales")
    print("=" * 60)

def show_subcategories(category_data, category_name):
    """Mostrar subcategorías de una categoría específica"""
    print(f"\n📋 SUBCATEGORÍAS DE '{category_name.upper()}':")
    print("=" * 60)
    
    for i, url_data in enumerate(category_data['urls'], 1):
        print(f"{i:2d}. {url_data['display_name']}")
    
    print(f"\n📊 Total: {len(category_data['urls'])} subcategorías")
    print("=" * 60)

def select_subcategories(category_data, category_name):
    """Permitir selección de subcategorías específicas"""
    show_subcategories(category_data, category_name)
    
    print("\n🎯 OPCIONES DE SELECCIÓN:")
    print("• 'all' o 'todos' para todas las subcategorías")
    print("• Número específico (ej: 1, 3, 5)")
    print("• Rango (ej: 1-3)")
    print("• Múltiples (ej: 1,3,5)")
    
    try:
        selection = input(f"\nSelecciona subcategorías (1-{len(category_data['urls'])} o 'all'): ").strip().lower()
        
        if selection in ['all', 'todos', 'todas']:
            selected_urls = [url_data['url'] for url_data in category_data['urls']]
            selected_names = [url_data['display_name'] for url_data in category_data['urls']]
            print(f"✅ Seleccionadas: TODAS las subcategorías ({len(selected_urls)})")
            return selected_urls, selected_names
        
        # Parsear selección
        selected_indices = []
        
        if '-' in selection:
            # Rango
            try:
                start, end = map(int, selection.split('-'))
                selected_indices = list(range(start, end + 1))
            except:
                print("❌ Formato de rango inválido")
                return [], []
        elif ',' in selection:
            # Múltiples
            try:
                selected_indices = [int(x.strip()) for x in selection.split(',')]
            except:
                print("❌ Formato de lista inválido")
                return [], []
        else:
            # Número único
            try:
                selected_indices = [int(selection)]
            except:
                print("❌ Número inválido")
                return [], []
        
        # Validar índices y crear listas
        selected_urls = []
        selected_names = []
        
        for idx in selected_indices:
            if 1 <= idx <= len(category_data['urls']):
                url_data = category_data['urls'][idx - 1]
                selected_urls.append(url_data['url'])
                selected_names.append(url_data['display_name'])
            else:
                print(f"⚠️ Índice {idx} fuera de rango")
        
        if selected_urls:
            print(f"✅ Seleccionadas {len(selected_urls)} subcategorías:")
            for name in selected_names:
                print(f"   • {name}")
        
        return selected_urls, selected_names
        
    except Exception as e:
        print(f"❌ Error en selección: {e}")
        return [], []

def ejecutar_scraper_proyecto(urls, categoria_nombre):
    """Ejecutar usando el proyecto scraper principal con configuración optimizada"""
    
    print("🍎 PLAZA VEA SCRAPER - PROYECTO PRINCIPAL")
    print("=" * 50)
    print(f"📂 Categoría: {categoria_nombre}")
    print(f"🔗 URLs a procesar: {len(urls)}")
    for i, url in enumerate(urls, 1):
        subcategoria = url.split('/')[-1].replace('-', ' ').title()
        print(f"   {i}. {subcategoria}")
    print("🚀 Iniciando crawler...")
    
    # Configuración para el proyecto scraper principal
    settings = {
        'BOT_NAME': 'scraper',
        'SPIDER_MODULES': ['scraper.spiders'],
        'NEWSPIDER_MODULE': 'scraper.spiders',
        
        # Configuración básica
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        
        # Scrapy-Playwright
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        
        # Delays optimizados
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        
        # Pipeline del proyecto principal para guardar en base de datos (PlazaVea - Perú)
        'ITEM_PIPELINES': {
            'scraper.pipelines.PostgresPipeline': 300,
        },
        
        # Logging
        'LOG_LEVEL': 'INFO',
        
        # Playwright settings
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            "headless": True,
            "timeout": 30000,
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        
        # Windows
        'TELNETCONSOLE_ENABLED': False,
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
        'FEED_EXPORT_ENCODING': 'utf-8',
        
        # Configuración de AutoThrottle
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': False,
        
        # Cache deshabilitado para datos frescos
        'HTTPCACHE_ENABLED': False,
        
        # Límite removido para procesamiento completo
        # 'CLOSESPIDER_ITEMCOUNT': 10,  # Comentado para obtener TODO
    }
    
    try:
        # Configurar asyncio para Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Cambiar al directorio del proyecto
        original_cwd = os.getcwd()
        scraper_dir = os.path.join(current_dir, 'scraper')
        os.chdir(scraper_dir)
        
        # Importar CrawlerProcess
        from scrapy.crawler import CrawlerProcess
        
        # Crear proceso crawler
        process = CrawlerProcess(settings)
        
        # Convertir URLs a string para el spider
        urls_str = ",".join(urls)
        
        # Ejecutar spider del proyecto principal
        process.crawl(
            'plaza_vea',  # nombre del spider en el proyecto scraper
            custom_urls=urls_str  # parámetro - múltiples URLs separadas por coma
        )
        
        # Ejecutar
        process.start()
        
        print("✅ Scraping completado")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restaurar directorio original
        try:
            os.chdir(original_cwd)
        except:
            pass

def main():
    """Función principal con selección avanzada para el proyecto scraper"""
    
    print("🍎 PLAZA VEA SCRAPER RUNNER")
    print("   🎯 Proyecto Principal + Selección Avanzada")
    print("   🗄️ Base de datos: Tabla 'peru'")
    print("=" * 60)
    
    # Obtener categorías desde constantes del proyecto scraper
    categories = get_categories_from_constants()
    
    if not categories:
        print("❌ No se pudieron cargar las categorías")
        print("💡 Verifica que existe scraper/scraper/spiders/constants/plaza_vea.py")
        return
    
    # Mostrar categorías
    show_categories(categories)
    
    try:
        # Selección de categoría
        selection = input(f"\nSelecciona categoría (1-{len(categories)}): ").strip()
        
        try:
            category_index = int(selection) - 1
            if not (0 <= category_index < len(categories)):
                print("❌ Número de categoría inválido")
                return
        except ValueError:
            print("❌ Entrada inválida")
            return
        
        # Obtener categoría seleccionada
        category_key = list(categories.keys())[category_index]
        category_data = categories[category_key]
        category_name = category_data['display_name']
        
        print(f"\n✅ Categoría seleccionada: {category_name}")
        
        # Selección de subcategorías
        selected_urls, selected_names = select_subcategories(category_data, category_name)
        
        if not selected_urls:
            print("❌ No se seleccionaron subcategorías válidas")
            return
        
        print(f"\n📊 RESUMEN:")
        print(f"   📂 Categoría: {category_name}")
        print(f"   📦 Subcategorías: {len(selected_urls)}")
        print(f"   🔗 URLs a procesar: {len(selected_urls)}")
        print(f"   🗄️ Destino: Tabla 'peru' en PostgreSQL")
        print(f"   🏪 Comercial: PlazaVea")
        
        confirm = input(f"\n¿Procesar {len(selected_urls)} subcategoría(s)? (s/n): ").lower().strip()
        if confirm not in ['s', 'si', 'y', 'yes']:
            print("❌ Operación cancelada")
            return
            
        # Ejecutar scraper usando el proyecto principal
        ejecutar_scraper_proyecto(selected_urls, f"{category_name} - {', '.join(selected_names)}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()