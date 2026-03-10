#!/bin/bash
# ============================================================
#  reenviar.sh — Ejecutable para reenviar el nuevo mensaje
# ============================================================
#  Ejecuta reenviar_mensaje.py con el entorno virtual.
#  Máximo 25 mensajes por día. No repite contactos.
#  Excluye +591 65317007.
#  Ejecutar cada día hasta que se terminen todos.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Descargar últimos cambios del repositorio remoto ──
if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$REMOTE_URL" ]; then
        echo "🔄 Sincronizando con repositorio remoto..."
        if git pull --rebase origin "$(git rev-parse --abbrev-ref HEAD)" 2>&1; then
            echo "✅ Código actualizado."
        else
            echo "⚠️  No se pudo descargar (sin conexión o conflicto). Continuando con versión local."
        fi
        echo ""
    fi
fi

# Verificar que existe el entorno virtual
if [ ! -f "venv/bin/python3" ]; then
    echo "❌ No se encontró el entorno virtual. Ejecutando setup..."
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt
    venv/bin/python3 -m playwright install chromium
fi

echo ""
echo "=========================================="
echo "  📤 REENVÍO DE MENSAJE NUEVO"
echo "  📅 $(date '+%Y-%m-%d %H:%M')"
echo "  🔢 Máximo 25 por día"
echo "=========================================="
echo ""

# Ejecutar el script de reenvío
venv/bin/python3 reenviar_mensaje.py

echo ""
echo "=========================================="
echo "  ✅ Proceso finalizado"
echo "  📅 $(date '+%Y-%m-%d %H:%M')"

# Mostrar progreso total
if [ -f "reenvio_progreso.csv" ]; then
    TOTAL_REENVIADOS=$(grep -c "Reenviado" reenvio_progreso.csv 2>/dev/null || echo "0")
    TOTAL_FALLIDOS=$(grep -c "Fallido" reenvio_progreso.csv 2>/dev/null || echo "0")
    echo "  📊 Total reenviados: $TOTAL_REENVIADOS"
    echo "  ❌ Total fallidos: $TOTAL_FALLIDOS"
fi

TOTAL_CONTACTADOS=$(grep -c "Enviado" contactados.csv 2>/dev/null || echo "0")
echo "  📋 Total contactos originales: $TOTAL_CONTACTADOS"
echo "=========================================="
echo ""
echo "Si quedan pendientes, ejecuta de nuevo mañana."
echo ""

# ── Guardar cambios y subir al repositorio remoto ──
bash "$SCRIPT_DIR/git_sync.sh" || true

read -rp "Presiona Enter para cerrar..."
