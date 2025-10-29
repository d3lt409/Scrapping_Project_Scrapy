# Constantes para el spider de Juriscol
import time

# URLs
BASE_URL = "https://www.suin-juriscol.gov.co"
START_URL = "https://www.suin-juriscol.gov.co/legislacion/normatividad.html"

# Selectores CSS para elementos de la página
SELECTORS = {
    # Botón para alternar respuesta (mostrar formulario)
    'TOGGLE_FORM_BUTTON': '#alternar-respuesta-ej1',
    
    # Formulario principal
    'MAIN_FORM': '#mainForm',
    
    # Tipo de norma
    'TIPO_NORMA_SELECT': 'select[name="tipo"]',
    'TIPO_NORMA_OPTION_DECRETOS': 'option[value="Decretos"]',
    'TIPO_NORMA_OPTION_LEYES': 'option[value="Leyes"]',
    'TIPO_NORMA_OPTION_RESOLUCION': 'option[value="Resolucion"]',
    
    # Sector
    'SECTOR_SELECT': 'select[name="sector"]',
    
    # Estado de vigencia
    'ESTADO_DOCUMENTO_SELECT': 'select[name="estado_documento"]',
    
    # Botón de búsqueda
    'BUSCAR_BUTTON': 'input[type="submit"]',
    'BUSCAR_BUTTON_ALT': 'input[value*="Consultar"]',
    'BUSCAR_BUTTON_ALT2': 'button[type="submit"]',
    
    # Resultados
    'RESULTS_TABLE': 'table.hitlist.legis',
    'RESULTS_ROWS': 'table.hitlist.legis tbody tr',
    'PAGINATION_INFO': '.searchResultsControl span',
    'NEXT_PAGE_BUTTON': 'img[src="../images/hitlist/arrow-right-icon.png"]',
    'LAST_PAGE_BUTTON': 'img[src="../images/hitlist/arrow-right-double-icon.png"]',
    
    # Columnas de la tabla
    'COLUMN_TIPO': 'td:nth-child(1)',
    'COLUMN_NUMERO': 'td:nth-child(2)',
    'COLUMN_ANO': 'td:nth-child(3)',
    'COLUMN_SECTOR': 'td:nth-child(4)',
    'COLUMN_EMISOR': 'td:nth-child(5)',
    'COLUMN_ESTADO': 'td:nth-child(6)',
    'COLUMN_EPIGRAFE': 'td:nth-child(7)',
    'COLUMN_ACCIONES': 'td:nth-child(8)',
    
    # Link del documento
    'DOCUMENT_LINK': 'a[href*="/viewDocument.asp"]'
}

# Tipos de norma disponibles
TIPOS_NORMA = {
    'DECRETOS': 'Decretos',
    'LEYES': 'Leyes',
    'RESOLUCION': 'Resolucion'
}

# Estados de vigencia prioritarios
ESTADOS_VIGENCIA_PRIORITARIOS = [
    'Vigente',
    'Vigente Parcial'
]

# Sectores prioritarios para scraping
SECTORES_PRIORITARIOS = [
    "Tecnologías de la Información y de las Comunicaciones",
    "Salud y Protección Social",
    "Transporte",
    "Hacienda y Crédito Público"
]

# Configuraciones de tiempo
DELAYS = {
    'FORM_SUBMIT': 3,  # Tiempo de espera después de enviar formulario
    'PAGE_LOAD': 2,    # Tiempo de espera para carga de página
    'NAVIGATION': 1    # Tiempo de espera para navegación
}

# Headers para las peticiones
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Parámetros para formulario
FORM_PARAMS = {
    'action': 'Consultar',
    'ordenar': 'Fecha'
}