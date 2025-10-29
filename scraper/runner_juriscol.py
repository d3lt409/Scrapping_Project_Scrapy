#!/usr/bin/env python3
"""
Runner sencillo para el spider Juriscol
Flujo mínimo: usa todos los sectores prioritarios y permite elegir tipos de norma
Opciones: "todos" o seleccionar por índices (ej. 1,3)
"""

import os
import sys
import subprocess
from scraper.spiders.constants.juriscol import SECTORES_PRIORITARIOS, TIPOS_NORMA


def mostrar_banner():
    print("=" * 60)
    print("SCRAPER JURISCOL - RUNNER SIMPLIFICADO")
    print("=" * 60)
    print("Selecciona sector y tipo de norma a procesar.")
    print("(Vigencias siempre: Vigente + Vigente Parcial)\n")


def mostrar_sectores():
    """Muestra los sectores disponibles"""
    print("SECTORES DISPONIBLES:")
    for i, sector in enumerate(SECTORES_PRIORITARIOS, 1):
        print(f"  {i}. {sector}")
    return SECTORES_PRIORITARIOS


def seleccionar_sectores():
    """Permite seleccionar uno o varios sectores"""
    sectores_lista = mostrar_sectores()
    print("\nElige: [Enter]=Todos  o ingresa números separados por coma (ej. 1,3)")
    entrada = input("Sectores a procesar: ").strip()
    
    if not entrada:
        return sectores_lista

    try:
        indices = [int(x.strip()) - 1 for x in entrada.split(',') if x.strip()]
        seleccion = []
        for idx in indices:
            if 0 <= idx < len(sectores_lista):
                seleccion.append(sectores_lista[idx])
            else:
                print(f"Índice fuera de rango: {idx + 1}")
                return None
        return seleccion
    except ValueError:
        print("Entrada inválida. Usa números separados por comas o presiona Enter para todos.")
        return None


def mostrar_tipos():
    """Muestra los tipos de norma disponibles"""
    print("TIPOS DE NORMA DISPONIBLES:")
    tipos = list(TIPOS_NORMA.values())
    for i, t in enumerate(tipos, 1):
        print(f"  {i}. {t}")
    return tipos


def seleccionar_tipos():
    """Permite seleccionar uno o varios tipos de norma"""
    tipos_lista = mostrar_tipos()
    print("\nElige: [Enter]=Todos  o ingresa números separados por coma (ej. 1,3)")
    entrada = input("Tipos a procesar: ").strip()
    
    if not entrada:
        return tipos_lista

    try:
        indices = [int(x.strip()) - 1 for x in entrada.split(',') if x.strip()]
        seleccion = []
        for idx in indices:
            if 0 <= idx < len(tipos_lista):
                seleccion.append(tipos_lista[idx])
            else:
                print(f"Índice fuera de rango: {idx + 1}")
                return None
        return seleccion
    except ValueError:
        print("Entrada inválida. Usa números separados por comas o presiona Enter para todos.")
        return None


def mostrar_resumen(sectores, tipos):
    print("\nRESUMEN:")
    print(f"  Sectores seleccionados: {len(sectores)}")
    for sector in sectores:
        print(f"    - {sector}")
    print(f"  Tipos seleccionados: {len(tipos)}")
    for tipo in tipos:
        print(f"    - {tipo}")
    print(f"  Vigencias: Vigente + Vigente Parcial (automático)")
    total = len(sectores) * len(tipos) * 2
    print(f"  Total combinaciones: {total}\n")


def ejecutar_spider(sectores, tipos):
    sectores_param = ','.join(sectores)
    tipos_param = ','.join(tipos)

    cmd = [
        sys.executable,
        "-m", "scrapy", "crawl", "juriscol",
        "-a", f"sectores={sectores_param}",
        "-a", f"tipos={tipos_param}"
    ]

    print("Ejecutando spider con los parametros indicados...")
    print(f"Comando: {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("Ejecucion interrumpida por el usuario")


def main():
    mostrar_banner()

    # 1. Seleccionar sectores
    print("1. SELECCIÓN DE SECTORES")
    sectores = None
    while sectores is None:
        sectores = seleccionar_sectores()
    
    print()
    
    # 2. Seleccionar tipos de norma
    print("2. SELECCIÓN DE TIPOS DE NORMA")
    tipos = None
    while tipos is None:
        tipos = seleccionar_tipos()

    mostrar_resumen(sectores, tipos)
    ejecutar_spider(sectores, tipos)



if __name__ == "__main__":
    main()