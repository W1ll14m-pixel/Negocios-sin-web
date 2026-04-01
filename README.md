# 🔍 Sistema de Prospección de Negocios Sin Web

Sistema semiautomático para encontrar negocios en Google Maps que **no tienen página web**, generar mensajes personalizados y enviarlos por WhatsApp.

---

## 📋 Estructura del Proyecto

```
SINPAGINASWEB/
├── main.py                 # 🎯 Script principal (menú interactivo)
├── config.py               # ⚙️ Configuración global
├── scraper_maps.py         # 🔍 Scraper de Google Maps (Playwright)
├── generador_mensajes.py   # ✉️ Generador de mensajes y links wa.me
├── whatsapp_sender.py      # 📤 Envío masivo via WhatsApp Web
├── exportador.py           # 💾 Exportación a CSV/Excel
├── requirements.txt        # 📦 Dependencias Python
├── setup.sh                # 🔧 Script de instalación
└── README.md               # 📖 Este archivo
```

---

## 🚀 Instalación Rápida

### Opción 1: Script automático (Linux)
```bash
cd ~/Escritorio/SINPAGINASWEB
chmod +x setup.sh
./setup.sh
```

### Opción 2: Manual
```bash
cd ~/Escritorio/SINPAGINASWEB

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegador Chromium para Playwright
playwright install chromium
playwright install-deps chromium
```

---

## ▶️ Cómo Usar

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar el sistema
python3 main.py
```

### Menú Principal:
1. **Buscar negocios** — Abre Google Maps, busca por término, filtra los que NO tienen web
2. **Cargar CSV** — Carga prospectos desde un archivo anterior
3. **Enviar por WhatsApp** — Envío masivo con pausas inteligentes anti-bloqueo
4. **Ver prospectos** — Muestra la lista actual en memoria
5. **Generar links** — Genera links wa.me para envío manual
6. **Configuración** — Ver/cambiar parámetros

---

## 🛡️ Sistema Anti-Bloqueo

El sistema incluye múltiples capas de protección:

| Protección | Detalle |
|------------|---------|
| **Pausas aleatorias** | 45-120 segundos entre cada mensaje |
| **Pausa larga** | 5-10 minutos cada 5 mensajes |
| **Límite por sesión** | Máximo 20 mensajes por sesión |
| **Detección de bloqueo** | Detecta textos de restricción y se pausa automáticamente |
| **Verificación de vinculación** | Verifica que WhatsApp Web esté conectado antes de enviar |
| **Re-verificación** | Cada 3 mensajes verifica que siga vinculado |

---

## ⚙️ Configuración

Edita `config.py` para personalizar:

- **`CODIGO_PAIS`**: Tu código de país (por defecto: `591` Bolivia)
- **`PLANTILLA_MENSAJE`**: El mensaje que se enviará
- **`PAUSA_MIN / PAUSA_MAX`**: Tiempos de espera del scraper
- **`ARCHIVO_CSV / ARCHIVO_EXCEL`**: Nombres de los archivos de salida

---

## 📱 Flujo de WhatsApp Web

1. El sistema abre WhatsApp Web en un navegador
2. Te pide escanear el código QR con tu teléfono
3. Verifica automáticamente que la vinculación sea exitosa
4. Confirma la conexión antes de empezar a enviar
5. Envía mensajes con pausas humanas
6. Si detecta bloqueo, se pausa automáticamente (1 hora)
7. Al terminar, guarda el estado de cada envío en CSV/Excel

---

## ⚠️ Advertencias Importantes

- **No abuses del envío masivo.** WhatsApp puede bloquear tu número permanentemente.
- **Usa un número secundario** para las pruebas iniciales.
- **El modo semiautomático (Opción 5: links)** es más seguro porque tú controlas cada envío.
- **Google Maps** puede bloquear tu IP si haces muchas búsquedas seguidas. Usa VPN si es necesario.

---

## 📊 Archivos Generados

- `prospectos.csv` — Datos de todos los negocios encontrados
- `prospectos.xlsx` — Mismo contenido en formato Excel
- `whatsapp_session/` — Datos de sesión de WhatsApp Web (no borrar si quieres mantener la vinculación)

---

## 💻 Configuración de VS Code + GitHub Copilot (Beneficios de Estudiante)

Este proyecto incluye configuración lista para usar con **GitHub Copilot** en VS Code.

### Requisitos previos

1. Tener una cuenta de **GitHub Education** activa (GitHub Student Developer Pack).
   - Verifica tu estado en: [education.github.com/discount_requests](https://education.github.com/discount_requests)
   - Si tu verificación está pendiente o rechazada, vuelve a solicitarla con una foto clara de tu credencial estudiantil.

2. Tener **GitHub Copilot** habilitado en tu cuenta:
   - Ve a [github.com/settings/copilot](https://github.com/settings/copilot)
   - Asegúrate de que el plan activo sea el **gratuito para estudiantes** (Free for students).

### Instalación de extensiones

Al abrir este repositorio en VS Code, recibirás una notificación para instalar las extensiones recomendadas:
- **GitHub Copilot** (`github.copilot`)
- **GitHub Copilot Chat** (`github.copilot-chat`)
- **Python** (`ms-python.python`)
- **Pylance** (`ms-python.vscode-pylance`)

Si no aparece la notificación, instálalas manualmente:
```
Ctrl+Shift+P → Extensions: Show Recommended Extensions
```

### Vincular VS Code con tu cuenta de GitHub

1. Abre VS Code.
2. Ve a **Cuentas** (ícono de persona en la barra lateral izquierda, parte inferior).
3. Haz clic en **Iniciar sesión con GitHub** y autoriza el acceso.
4. Verifica que aparezca tu nombre de usuario de GitHub.

### Acceso a modelos de IA (Claude Opus y otros)

GitHub Copilot Chat permite seleccionar el modelo de IA directamente desde la interfaz:

1. Abre el panel de **Copilot Chat** (`Ctrl+Alt+I`).
2. Haz clic en el **selector de modelo** (ícono de chispa ✦ junto al campo de texto).
3. Selecciona el modelo deseado, por ejemplo `claude-opus-4`.

> **⚠️ Nota sobre modelos bloqueados:** Si un modelo como `Claude Opus` aparece como no disponible, puede deberse a:
> - Tu plan de Copilot no incluye ese modelo (los planes gratuitos para estudiantes pueden tener restricciones de modelos premium).
> - La verificación de estudiante aún no está activa. Espera 1-2 días hábiles tras la aprobación.
> - Necesitas actualizar la extensión de Copilot Chat a la última versión.
>
> **Solución:** Verifica en [github.com/settings/copilot](https://github.com/settings/copilot) que tu suscripción esté activa y que los modelos adicionales estén habilitados en **"Policies"**.

### Solución de problemas comunes

| Problema | Solución |
|----------|----------|
| Copilot no sugiere código | Verifica que hayas iniciado sesión (`Ctrl+Shift+P → GitHub Copilot: Sign In`) |
| "No tienes acceso a Copilot" | Revisa el estado de tu suscripción en github.com/settings/copilot |
| Modelo bloqueado | El plan gratuito de estudiante puede no incluir modelos premium; revisa las políticas de tu cuenta |
| La vinculación falla | Cierra sesión y vuelve a iniciar sesión desde VS Code: `Ctrl+Shift+P → GitHub: Sign Out` |
