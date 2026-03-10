#!/bin/bash
# ============================================================
#  git_sync.sh — Guardado automático al repositorio remoto
# ============================================================
#  Se ejecuta al final de cualquier script del sistema.
#  Pasos: add → commit (si hay cambios) → push
#  Nunca detiene el proceso principal si falla.
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  💾 GUARDANDO CAMBIOS EN REPOSITORIO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── PASO 1: Verificar que git está disponible ──────────────
echo ""
echo "  [1/5] Verificando git..."
if ! command -v git &>/dev/null; then
    echo "  ❌ Git no está instalado. Saltando sincronización."
    exit 0
fi
echo "  ✅ Git disponible: $(git --version)"

# ── PASO 2: Verificar que estamos dentro de un repositorio ─
echo ""
echo "  [2/5] Verificando repositorio..."
if ! git rev-parse --git-dir &>/dev/null; then
    echo "  ❌ No es un repositorio Git. Saltando sincronización."
    exit 0
fi
echo "  ✅ Repositorio: $(git rev-parse --show-toplevel)"

# ── PASO 3: Verificar que existe remote configurado ────────
echo ""
echo "  [3/5] Verificando conexión al remoto..."
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "  ❌ No hay repositorio remoto configurado (origin)."
    exit 0
fi
echo "  ✅ Remoto: $REMOTE_URL"

# ── PASO 4: Agregar todos los cambios al staging ───────────
echo ""
echo "  [4/5] Agregando cambios al staging (git add)..."
git add -A
ESTADO=$(git status --short)
if [ -z "$ESTADO" ]; then
    echo "  ℹ️  Sin cambios nuevos. El repositorio ya está al día."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ Repositorio sincronizado (sin cambios)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi
echo "  ✅ Archivos a guardar:"
git status --short | sed 's/^/     /'

# ── PASO 5: Commit con timestamp ───────────────────────────
echo ""
echo "  [5/5] Creando commit y subiendo al remoto..."
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
RAMA=$(git rev-parse --abbrev-ref HEAD)

if git commit -m "sync: actualización automática del sistema [$TIMESTAMP]"; then
    echo "  ✅ Commit creado correctamente"
else
    echo "  ❌ Error al crear el commit."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ❌ Sincronización fallida en commit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

# ── PUSH ────────────────────────────────────────────────────
echo ""
echo "  📡 Subiendo a origin/$RAMA..."
if git push origin "$RAMA"; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ CAMBIOS GUARDADOS Y SUBIDOS"
    echo "  📅 $TIMESTAMP"
    echo "  🌿 Rama: $RAMA"
    ULTIMO_COMMIT=$(git log --oneline -1)
    echo "  📌 Commit: $ULTIMO_COMMIT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚠️  Commit guardado localmente."
    echo "  ❌ No se pudo subir al remoto (sin internet?)."
    echo "  ℹ️  Ejecuta: git push origin $RAMA"
    echo "  ℹ️  cuando tengas conexión."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
