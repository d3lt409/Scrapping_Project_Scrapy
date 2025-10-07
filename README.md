# Proyecto de Web Scraping de Precios para Retail

## 1. Resumen General

Este proyecto consiste en un sistema de web scraping avanzado y robusto, diseñado para recolectar sistemáticamente datos de precios de productos en sitios de e-commerce de retail. La arquitectura está construida para ser escalable y resiliente, capaz de manejar sitios web modernos y complejos que utilizan cargas dinámicas de contenido, paginación avanzada y protecciones anti-scraping.

Los datos recolectados se almacenan de forma estructurada en una base de datos **PostgreSQL**, listos para su posterior análisis, visualización o uso en modelos de negocio.

**Tecnologías Principales:**
* **Framework:** Scrapy
* **Automatización de Navegador:** Playwright
* **Base de Datos:** PostgreSQL
* **Lenguaje:** Python

---

## 2. Características Principales

* **Arquitectura Híbrida (Scrapy + Playwright):** Combina la alta velocidad y concurrencia de Scrapy con la capacidad de Playwright para renderizar JavaScript y manejar sitios dinámicos, obteniendo lo mejor de ambos mundos.
* **Descubrimiento Dinámico de Subcategorías:** Las arañas no dependen de listas de URLs fijas. Navegan los menús de los sitios, simulando el comportamiento humano (clics y hovers) para descubrir y scrapear todas las subcategorías de productos, asegurando una cobertura de datos completa.
* **Manejo de Carga "Perezosa" (Lazy Loading):** Implementa un bucle de scroll inteligente que mide la altura del contenedor de productos, garantizando que todos los ítems se carguen en la vista antes de iniciar la extracción.
* **Paginación Avanzada:** Capaz de manejar lógicas de paginación complejas donde los botones de "Siguiente" son dinámicos o están basados en la posición del elemento activo.
* **Procesamiento y Limpieza de Datos:** Extrae, limpia y formatea los datos en tiempo de ejecución, separando valores numéricos de unidades de medida para facilitar el análisis.
* **Persistencia en Base de Datos:** Utiliza los `Item Pipelines` de Scrapy para almacenar de forma segura y estructurada toda la información en una base de datos PostgreSQL.

---

## 3. Arañas (Spiders) Implementadas

### a) `jumbo_spider.py`
* **Sitio:** Jumbocolombia.com
* **Retos Superados:**
    * Implementa un "director de orquesta" que primero determina si una categoría tiene demasiados productos (ej: >1400).
    * Si es así, ejecuta un proceso de **descubrimiento por hover** para scrapear las subcategorías.
    * Si no, scrapea la categoría directamente.
    * Maneja una lógica de **paginación por "hermano siguiente" (following-sibling)**, identificando el botón de página activa y haciendo clic en el siguiente.
    * Utiliza el **scroll inteligente por medición de contenedor** para cargar todos los productos.

### b) `cruzverde_spider.py`
* **Sitio:** Cruzverde.com.co
* **Retos Superados:**
    * Maneja pop-ups y modales iniciales de selección de ubicación.
    * Utiliza una estrategia de paginación y scroll adaptada a la estructura específica del sitio.
    * Demuestra la modularidad del proyecto, donde la lógica de extracción (`take_products_fields`) puede ser adaptada para diferentes estructuras de "cards" de productos.

---

## 4. Prerrequisitos

Asegúrate de tener instalado el siguiente software en tu sistema (ya sea local o en WSL):

* Python (versión 3.9 o superior)
* PostgreSQL (versión 12 o superior)
* Git

---

## 5. Instalación y Configuración

**1. Clonar el Repositorio:**
```bash
git clone <url-de-tu-repositorio>
cd <nombre-del-repositorio>
