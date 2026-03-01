# ============================================================
# config.py — Configuración global del sistema de prospección
# ============================================================

# --- Código de país por defecto (Bolivia = 591) ---
# Cámbialo al código de tu país si es necesario
CODIGO_PAIS = "591"

# --- Ciudad / Zona donde buscar ---
CIUDAD = "Cochabamba"

# --- Límite de MENSAJES DIARIOS (seguridad contra bloqueos de WhatsApp) ---
# WhatsApp bloquea después de ~15-20 mensajes a números nuevos por día
# Usar 10 como límite seguro
MENSAJES_DIARIOS_MAX = 10

# --- Cantidad de negocios a buscar por cada categoría ---
# Se ajusta automáticamente para alcanzar MENSAJES_DIARIOS_MAX
CANTIDAD_POR_CATEGORIA = 3  # 3 x múltiples categorías = MENSAJES_DIARIOS_MAX

# --- Categorías de negocios a buscar automáticamente ---
# El sistema recorrerá ESTAS categorías hasta alcanzar MENSAJES_DIARIOS_MAX
CATEGORIAS_NEGOCIOS = [
    "Restaurantes",
    "Pizzerías",
    "Cafeterías",
    "Panaderías",
    "Peluquerías",
    "Barberías",
    "Talleres mecánicos",
    "Ferreterías",
    "Tiendas de ropa",
    "Zapaterías",
    "Gimnasios",
    "Dentistas",
    "Clínicas veterinarias",
    "Lavanderías",
    "Librerías",
    "Floristerías",
    "Joyerías",
    "Ópticas",
    "Farmacias",
    "Hoteles",
    "Hostales",
    "Constructoras",
    "Imprentas",
    "Estudios fotográficos",
    "Academias",
    "Escuelas de manejo",
    "Cerrajerías",
    "Carpinterías",
    "Tornerías",
    "Salones de belleza",
    "Spa",
    "Centros de masajes",
    "Consultorios médicos",
    "Abogados",
    "Contadores",
    "Arquitectos",
    "Electricistas",
    "Plomeros",
    "Carnicerías",
    "Fruterías",
    "Heladerías",
    "Pastelerías",
    "Pollerías",
    "Comida rápida",
    "Licorerías",
    "Minimarkets",
    "Papelerías",
    "Jugueterías",
    "Mueblerías",
    "Electrodomésticos",
]

# --- Archivo de control de contactos ya enviados ---
ARCHIVO_CONTACTADOS = "contactados.csv"
ARCHIVO_HISTORICO = "historico_contactos.csv"

# --- Pausas anti-bloqueo (en segundos) ---
PAUSA_MIN = 3          # Mínimo de espera entre acciones
PAUSA_MAX = 7          # Máximo de espera entre acciones
PAUSA_SCROLL_MIN = 2   # Pausa mínima al hacer scroll en Maps
PAUSA_SCROLL_MAX = 4   # Pausa máxima al hacer scroll en Maps

# --- Límites de seguridad ---
MAX_SCROLLS_SIN_RESULTADOS = 5   # Scrolls consecutivos sin nuevos resultados antes de parar
TIMEOUT_PAGINA = 60000            # Timeout para cargar páginas (ms)
TIMEOUT_ELEMENTO = 15000          # Timeout para esperar elementos (ms)

# --- Plantilla del mensaje personalizado ---
# Variables disponibles: {nombre_negocio}, {link_maps}
PLANTILLA_MENSAJE = (
    "Hola *{nombre_negocio}* 👋\n\n"
    "Los encontré en Google Maps aquí:\n"
    "📍 {link_maps}\n\n"
    "Noté que no tienen página web y me gustaría ofrecerles "
    "crear una *página web profesional* para su negocio.\n\n"
    "✅ Diseño moderno y adaptado a celulares\n"
    "✅ Aparece en Google cuando busquen su negocio\n"
    "✅ Catálogo de productos/servicios\n"
    "✅ Botón de contacto directo por WhatsApp\n"
    "✅ *Incluye subida al internet* (hosting)\n\n"
    "💰 Precio: *500 Bs* (negociable) — todo incluido.\n\n"
    "¿Les interesaría que les muestre algunos ejemplos? 😊"
)

# --- Archivo de salida ---
ARCHIVO_CSV = "prospectos.csv"
ARCHIVO_EXCEL = "prospectos.xlsx"

# --- User Agent para el navegador ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
