#!/bin/bash
# ============================================================
#  continuar_envio.sh — Retoma el envío de WhatsApp
#                       desde donde se interrumpió
# ============================================================
#  Usa los prospectos pendientes del CSV sin hacer
#  nueva búsqueda. Ideal cuando se cerró el sistema
#  a mitad del envío.
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
            echo "⚠️  No se pudo descargar. Continuando con versión local."
        fi
        echo ""
    fi
fi

# ── Verificar entorno virtual ──
if [ ! -f "venv/bin/python3" ]; then
    echo "❌ No se encontró el entorno virtual. Ejecutando setup..."
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt
    venv/bin/python3 -m playwright install chromium
fi

echo ""
echo "=========================================="
echo "  ▶  CONTINUANDO ENVÍO INTERRUMPIDO"
echo "  📅 $(date '+%Y-%m-%d %H:%M')"
echo "  📋 Solo procesa pendientes del CSV"
echo "=========================================="
echo ""

# ── Ejecutar envío de pendientes ──
venv/bin/python3 enviar_pendientes.py

echo ""
echo "=========================================="
echo "  ✅ Proceso finalizado"
echo "  📅 $(date '+%Y-%m-%d %H:%M')"
echo "=========================================="
echo ""

# ── Guardar cambios y subir al repositorio remoto ──
bash "$SCRIPT_DIR/git_sync.sh" || true

read -rp "Presiona Enter para cerrar..."
