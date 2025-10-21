# Imagen base estable con Python + Playwright + Chromium ya instalado
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble


# Establecemos la ruta de trabajo de Lambda
WORKDIR /var/task

# Configura los permisos
RUN chmod -R 755 /var/task

# Copiamos el código de tu proyecto
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# --- ¡CAMBIO CLAVE! ---
# El comando por defecto ahora es simplemente ejecutar Scrapy.
CMD ["scrapy", "crawl", "jumbo", "--loglevel", "INFO", "-a", "category=super", "-a", "part=1"]
