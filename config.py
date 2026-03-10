# ============================================================
# config.py — Configuración global del sistema de prospección
# ============================================================

# --- Código de país por defecto (Bolivia = 591) ---
CODIGO_PAIS = "591"

# --- META DIARIA DE MENSAJES ---
# El sistema completará esta cantidad cada vez que se ejecute,
# descontando los que ya se enviaron hoy.
MENSAJES_DIARIOS_META = 50

# --- Cantidad de negocios a buscar por cada categoría ---
CANTIDAD_POR_CATEGORIA = 5

# --- Ciudades de Bolivia (SECUENCIAL: se agota una antes de pasar a la siguiente) ---
# Primero TODO el departamento de Cochabamba, luego otros departamentos.
CIUDADES_BOLIVIA = [
    # ── Departamento de Cochabamba (PRIMERO) ──
    "Cochabamba",
    "Sacaba",
    "Quillacollo",
    "Colcapirhua",
    "Tiquipaya",
    "Vinto",
    "Punata",
    "Cliza",
    # ── Departamento de Santa Cruz ──
    "Santa Cruz de la Sierra",
    "Montero",
    "Warnes",
    "Camiri",
    # ── Departamento de La Paz ──
    "La Paz",
    "El Alto",
    # ── Departamento de Chuquisaca ──
    "Sucre",
    # ── Departamento de Oruro ──
    "Oruro",
    # ── Departamento de Tarija ──
    "Tarija",
    "Yacuiba",
    "Bermejo",
    "Villazón",
    # ── Departamento de Potosí ──
    "Potosí",
    "Tupiza",
    # ── Departamento de Beni ──
    "Trinidad",
    "Riberalta",
    "Guayaramerín",
    # ── Departamento de Pando ──
    "Cobija",
]

# Ciudad actual (se actualiza automáticamente según progreso)
CIUDAD = CIUDADES_BOLIVIA[0]

# Archivos de progreso de ciudades
ARCHIVO_CIUDAD_ACTUAL = "ciudad_actual.txt"
ARCHIVO_CIUDADES_COMPLETADAS = "ciudades_completadas.csv"

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
    "Estimados {nombre_negocio}, un cordial saludo.\n\n"
    "Me pongo en contacto con ustedes tras encontrar su ubicación a través de Google Maps:\n"
    "📍 {link_maps}\n\n"
    "He notado que actualmente no cuentan con un sitio web. Me gustaría poner a su disposición "
    "mis servicios para el desarrollo de una página web profesional, ideal para proyectar una "
    "mejor imagen de su negocio a sus clientes.\n\n"
    "El servicio incluye:\n"
    "✅ *Diseño moderno y responsivo:* Completamente adaptado para verse bien en celulares y computadoras.\n"
    "✅ *Presencia digital:* Su página estará publicada, activa y accesible en internet a través de un enlace directo.\n"
    "✅ *Catálogo integrado:* Una sección dedicada a mostrar sus productos o servicios de forma atractiva.\n"
    "✅ *Contacto ágil:* Botón de redirección directa para que los clientes les escriban a WhatsApp.\n"
    "✅ *Gestión técnica:* El servicio incluye la subida a internet y la configuración del alojamiento (hosting).\n\n"
    "👔 *Promoción Especial por el Mes del Padre:* Para apoyar a los negocios durante este mes, "
    "estoy ofreciendo la creación y configuración completa de la página por un pago único promocional de *200 Bs*.\n\n"
    "¿Me permitirían enviarles algunos ejemplos de mi trabajo sin ningún tipo de compromiso? "
    "Quedo atento a su respuesta.\n\n"
    "Atentamente, William Lujan Arispe"
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
