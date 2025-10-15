#!/usr/bin/env python3
"""
Script para verificar los XPath correctos de InkaFarma
Usa los XPath proporcionados por el usuario
"""

import asyncio
from playwright.async_api import async_playwright
import time

# CSS selectors corregidos basados en estructura real encontrada
SELECTORS = {
    'PRODUCT_CARD': "fp-product-small-category",
    'PRODUCT_NAME': "fp-product-name span",
    'PRODUCT_DESCRIPTION': "fp-product-description span", 
    'PRODUCT_PRICE': "fp-product-card-price span"
}

async def verificar_selectores():
    async with async_playwright() as p:
        print("🔍 Iniciando verificación de XPath en InkaFarma...")
        
        # Lanzar navegador
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navegar a la página
            print("📄 Navegando a InkaFarma...")
            await page.goto('https://inkafarma.pe/categoria/farmacia', timeout=90000, wait_until='domcontentloaded')
            
            # Esperar carga inicial
            print("⏳ Esperando carga de contenido...")
            await page.wait_for_timeout(10000)
            
            # Hacer scroll para activar lazy loading y esperar productos reales
            print("📜 Haciendo scroll para cargar productos...")
            await page.evaluate("window.scrollTo(0, 800)")
            await page.wait_for_timeout(5000)
            
            await page.evaluate("window.scrollTo(0, 1600)")
            await page.wait_for_timeout(5000)
            
            # Esperar a que aparezcan productos reales (no skeletons)
            print("⏳ Esperando productos reales...")
            try:
                # Esperar hasta que NO haya skeletons y SÍ haya productos reales
                await page.wait_for_function("""
                    () => {
                        const skeletons = document.querySelectorAll('fp-product-small-skeleton, fp-product-large-skeleton');
                        const realProducts = document.querySelectorAll('fp-product-small-category');
                        return skeletons.length === 0 && realProducts.length > 0;
                    }
                """, timeout=30000)
                print("✅ Productos reales cargados!")
            except:
                print("⚠️  Timeout esperando productos, procediendo con lo que hay...")
            
            # Buscar las tarjetas de productos
            print("🎯 Buscando tarjetas de productos...")
            product_cards = await page.locator(SELECTORS['PRODUCT_CARD']).all()
            print(f"✅ Encontradas {len(product_cards)} tarjetas de producto")
            
            if len(product_cards) == 0:
                print("❌ No se encontraron tarjetas de productos")
                
                # Debug: ver qué elementos fp-* existen
                print("\n🔍 Buscando TODOS los elementos fp-* en la página...")
                fp_elements = await page.locator("//*[starts-with(name(), 'fp-')]").all()
                for i, elem in enumerate(fp_elements[:30]):  # Mostrar más elementos
                    tag_name = await elem.evaluate("el => el.tagName")
                    print(f"  {i+1}. {tag_name}")
                
                # Buscar elementos que contengan "product" en su nombre
                print("\n🔍 Buscando elementos que contengan 'product'...")
                product_elements = await page.locator("//*[contains(name(), 'product')]").all()
                for i, elem in enumerate(product_elements[:10]):
                    tag_name = await elem.evaluate("el => el.tagName")
                    print(f"  {i+1}. {tag_name}")
                
                # Buscar divs con clases que puedan ser productos
                print("\n🔍 Buscando divs con clases de productos...")
                div_elements = await page.locator("div[class*='product'], div[class*='card'], div[class*='item']").all()
                print(f"  Encontrados {len(div_elements)} divs con clases relacionadas")
                
                # Ver el HTML completo de la página para debug
                print("\n🔍 Obteniendo estructura de la página...")
                try:
                    page_content = await page.content()
                    # Buscar fp-product en el contenido
                    if 'fp-product' in page_content:
                        print("✅ fp-product encontrado en el HTML")
                        import re
                        matches = re.findall(r'<fp-product[^>]*>', page_content)
                        for match in matches[:5]:
                            print(f"  {match}")
                    else:
                        print("❌ fp-product NO encontrado en el HTML")
                        
                    # Contar elementos por tipo
                    fp_count = page_content.count('<fp-')
                    print(f"📊 Total de elementos <fp-*>: {fp_count}")
                except Exception as e:
                    print(f"❌ Error obteniendo contenido: {e}")
                
                return
            
            # Analizar los primeros productos
            print(f"\n📦 Analizando los primeros {min(5, len(product_cards))} productos:")
            
            for i, card in enumerate(product_cards[:5]):
                print(f"\n--- Producto {i+1} ---")
                
                # Nombre del producto
                try:
                    name_elem = card.locator(SELECTORS['PRODUCT_NAME'])
                    name = await name_elem.text_content() if await name_elem.count() > 0 else "NO ENCONTRADO"
                    print(f"📝 Nombre: {name}")
                except Exception as e:
                    print(f"❌ Error en nombre: {e}")
                
                # Descripción del producto
                try:
                    desc_elem = card.locator(SELECTORS['PRODUCT_DESCRIPTION'])
                    desc = await desc_elem.text_content() if await desc_elem.count() > 0 else "NO ENCONTRADO"
                    print(f"📋 Descripción: {desc}")
                except Exception as e:
                    print(f"❌ Error en descripción: {e}")
                
                # Precio del producto
                try:
                    price_elem = card.locator(SELECTORS['PRODUCT_PRICE'])
                    price = await price_elem.text_content() if await price_elem.count() > 0 else "NO ENCONTRADO"
                    print(f"💰 Precio: {price}")
                except Exception as e:
                    print(f"❌ Error en precio: {e}")
                
                # Debug: mostrar estructura interna
                print("🔍 Estructura interna:")
                try:
                    inner_html = await card.inner_html()
                    # Mostrar solo las primeras líneas para no saturar
                    lines = inner_html.split('\n')[:5]
                    for line in lines:
                        if line.strip():
                            print(f"  {line.strip()[:100]}...")
                except Exception as e:
                    print(f"❌ Error obteniendo estructura: {e}")
        
        except Exception as e:
            print(f"❌ Error general: {e}")
        
        finally:
            print("\n🔚 Cerrando navegador...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(verificar_selectores())