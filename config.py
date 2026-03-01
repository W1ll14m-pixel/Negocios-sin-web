# ============================================================
# config.py — Configuración global del sistema de prospección
# ============================================================

# --- Código de país por defecto (Bolivia = 591) ---
CODIGO_PAIS = "591"

# --- META DIARIA DE MENSAJES ---
# El sistema completará esta cantidad cada vez que se ejecute,
# descontando los que ya se enviaron hoy.
MENSAJES_DIARIOS_META = 20

# --- Cantidad de negocios a buscar por cada categoría ---
CANTIDAD_POR_CATEGORIA = 5

# --- Ciudades de Bolivia (se busca en orden, rotando) ---
CIUDADES_BOLIVIA = [
    "Cochabamba",
    "Santa Cruz de la Sierra",
    "La Paz",
    "El Alto",
    "Sucre",
    "Oruro",
    "Tarija",
    "Potosí",
    "Trinidad",
    "Cobija",
    "Sacaba",
    "Quillacollo",
    "Montero",
    "Warnes",
    "Yacuiba",
    "Riberalta",
    "Guayaramerín",
    "Villazón",
    "Bermejo",
    "Camiri",
    "Tupiza",
    "Colcapirhua",
    "Tiquipaya",
    "Vinto",
    "Punata",
    "Cliza",
]

# Ciudad actual (se actualiza automáticamente al rotar)
CIUDAD = CIUDADES_BOLIVIA[0]

# --- Categorías de negocios (AMPLIADAS) ---
CATEGORIAS_NEGOCIOS = [
    # Gastronomía
    "Restaurantes", "Pizzerías", "Cafeterías", "Panaderías",
    "Heladerías", "Pastelerías", "Pollerías", "Comida rápida",
    "Churrasquerías", "Cevicherías", "Comida china", "Comida mexicana",
    "Comida japonesa", "Salteñerías", "Hamburgeserías", "Snacks",
    "Juguerías", "Açaí", "Food trucks", "Catering",
    # Belleza y cuidado personal
    "Peluquerías", "Barberías", "Salones de belleza", "Spa",
    "Centros de masajes", "Manicure y pedicure", "Centros de estética",
    "Depilación", "Tatuajes", "Maquillaje profesional",
    # Salud
    "Dentistas", "Consultorios médicos", "Clínicas veterinarias",
    "Farmacias", "Ópticas", "Fisioterapia", "Nutricionistas",
    "Psicólogos", "Laboratorios clínicos", "Consultorios oftalmológicos",
    # Servicios profesionales
    "Abogados", "Contadores", "Arquitectos", "Ingenieros civiles",
    "Notarías", "Consultoras", "Agencias de publicidad",
    "Diseñadores gráficos", "Traductores", "Agentes de seguros",
    # Comercio
    "Tiendas de ropa", "Zapaterías", "Joyerías", "Librerías",
    "Floristerías", "Jugueterías", "Mueblerías", "Electrodomésticos",
    "Ferreterías", "Papelerías", "Licorerías", "Minimarkets",
    "Tiendas de celulares", "Tiendas de computadoras", "Ópticas",
    "Tiendas de mascotas", "Tiendas deportivas", "Tiendas de bicicletas",
    "Perfumerías", "Tiendas de cosméticos", "Bazares",
    "Tiendas de telas", "Mercerías",
    # Servicios técnicos
    "Talleres mecánicos", "Electricistas", "Plomeros", "Cerrajerías",
    "Carpinterías", "Tornerías", "Vidrerías", "Tapicerías",
    "Reparación de celulares", "Reparación de computadoras",
    "Reparación de electrodomésticos", "Soldaduras", "Pintores",
    "Alarmas y seguridad", "Aire acondicionado",
    # Educación
    "Academias", "Escuelas de manejo", "Institutos de idiomas",
    "Guarderías", "Centros de tutorías", "Academias de música",
    "Academias de baile", "Academias de cocina",
    # Turismo y hospedaje
    "Hoteles", "Hostales", "Alojamientos", "Agencias de viaje",
    "Rent a car", "Transporte turístico",
    # Construcción e inmobiliaria
    "Constructoras", "Inmobiliarias", "Corralones",
    "Pisos y cerámicas", "Pinturerías", "Materiales de construcción",
    # Otros servicios
    "Imprentas", "Estudios fotográficos", "Lavanderías",
    "Tintorería", "Fumigación", "Mudanzas", "Limpieza profesional",
    "Decoración de eventos", "Alquiler de salones", "DJ y sonido",
    "Serigrafía", "Bordados", "Sastrería", "Funerarias",
    "Gimnasios", "Centros deportivos", "Yoga", "CrossFit",
    "Estacionamientos", "Lavado de autos", "Autolavados",
]

# --- Archivos de control ---
ARCHIVO_CONTACTADOS = "contactados.csv"
ARCHIVO_HISTORICO = "historico_contactos.csv"
ARCHIVO_CATEGORIAS_BUSCADAS = "categorias_buscadas.csv"

# --- Pausas anti-bloqueo (en segundos) ---
PAUSA_MIN = 3
PAUSA_MAX = 7
PAUSA_SCROLL_MIN = 2
PAUSA_SCROLL_MAX = 4

# --- Límites de seguridad ---
MAX_SCROLLS_SIN_RESULTADOS = 5
TIMEOUT_PAGINA = 60000
TIMEOUT_ELEMENTO = 15000

# --- Plantilla del mensaje personalizado ---
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
