#!/usr/bin/env bash
# ============================================================
#  ejecutar.sh — Doble clic para ejecutar el sistema
# ============================================================
#  Abre una terminal y ejecuta el sistema automáticamente.
#  Si no hay entorno virtual, lo crea e instala todo.
#  Funciona en cualquier dispositivo Linux/macOS.
# ============================================================

set -e

# ── Ir al directorio donde está este script (funciona desde cualquier lugar) ──
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================"
echo "  SISTEMA AUTOMATICO DE PROSPECCION SIN WEB"
echo "============================================"
echo ""

# ── Verificar que Python3 esté instalado ──
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no esta instalado."
    echo ""
    echo "Instalalo segun tu sistema operativo:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    echo "  macOS:         brew install python3"
    echo ""
    echo "Presiona Enter para salir..."
    read -r
    exit 1
fi

echo "Python3 encontrado: $(python3 --version)"

# ── Verificar que python3-venv esté disponible ──
if ! python3 -m venv --help &> /dev/null; then
    echo ""
    echo "ERROR: El modulo 'venv' de Python no esta instalado."
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    echo "  Fedora:        sudo dnf install python3-libs"
    echo ""
    echo "Presiona Enter para salir..."
    read -r
    exit 1
fi

# ── Crear entorno virtual si no existe ──
PYTHON_VENV=""
if [ -f "venv/bin/python3" ]; then
    PYTHON_VENV="venv/bin/python3"
elif [ -f "venv/bin/python" ]; then
    PYTHON_VENV="venv/bin/python"
fi

if [ -z "$PYTHON_VENV" ]; then
    echo ""
    echo "Primera ejecucion detectada. Configurando entorno..."
    echo ""

    echo "[1/4] Creando entorno virtual..."
    python3 -m venv venv

    # Determinar el ejecutable de Python dentro del venv
    if [ -f "venv/bin/python3" ]; then
        PYTHON_VENV="venv/bin/python3"
    elif [ -f "venv/bin/python" ]; then
        PYTHON_VENV="venv/bin/python"
    else
        echo "ERROR: No se pudo crear el entorno virtual."
        echo "Presiona Enter para salir..."
        read -r
        exit 1
    fi

    echo "[2/4] Actualizando pip..."
    "$PYTHON_VENV" -m pip install --upgrade pip --quiet

    echo "[3/4] Instalando dependencias de Python..."
    "$PYTHON_VENV" -m pip install -r requirements.txt --quiet

    echo "[4/4] Instalando navegador Chromium para Playwright..."
    "$PYTHON_VENV" -m playwright install chromium
    "$PYTHON_VENV" -m playwright install-deps chromium 2>/dev/null || true

    echo ""
    echo "Configuracion completada."
    echo "============================================"
    echo ""
fi

# ── Verificar que las dependencias estén instaladas ──
if ! "$PYTHON_VENV" -c "import playwright, pandas, rich" 2>/dev/null; then
    echo ""
    echo "Dependencias faltantes detectadas. Instalando..."
    "$PYTHON_VENV" -m pip install -r requirements.txt --quiet
    "$PYTHON_VENV" -m playwright install chromium
    "$PYTHON_VENV" -m playwright install-deps chromium 2>/dev/null || true
    echo "Dependencias instaladas."
    echo ""
fi

# ── Ejecutar el sistema ──
echo "Iniciando sistema..."
echo ""
"$PYTHON_VENV" main.py

# ── Guardar cambios y subir al repositorio remoto ──
bash "$DIR/git_sync.sh" || true

# ── Mostrar resultado y esperar ──
echo ""
echo "============================================"
echo "  Sistema finalizado."
echo "============================================"
echo ""
echo "Presiona Enter para cerrar..."
read -r
