#!/usr/bin/env bash
# ============================================================
# setup.sh — Configuración inicial del entorno de desarrollo
# Ejecutar UNA VEZ después de clonar el repositorio.
#
# Uso: bash scripts/setup.sh
#      make setup
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}→${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
error()   { echo -e "${RED}✗${NC} $1"; exit 1; }

echo ""
echo "  Taller Inspección — Setup de desarrollo"
echo "  ========================================"
echo ""

# ----------------------------------------------------------------
# Verificar prerrequisitos
# ----------------------------------------------------------------
info "Verificando prerrequisitos..."

command -v python3 >/dev/null 2>&1 || error "Python 3.12+ requerido. Ver: docs/SETUP.md"
command -v pip >/dev/null 2>&1 || error "pip requerido."
command -v git >/dev/null 2>&1 || error "git requerido."

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 12 ]]; then
  error "Python 3.12+ requerido. Versión actual: $PYTHON_VERSION"
fi
success "Python $PYTHON_VERSION detectado"

# Flutter (opcional — solo para desarrollo de apps)
if command -v flutter >/dev/null 2>&1; then
  FLUTTER_VERSION=$(flutter --version 2>&1 | head -1 | awk '{print $2}')
  success "Flutter $FLUTTER_VERSION detectado"
else
  warn "Flutter no encontrado — solo necesario para apps mobile/web"
fi

# Firebase CLI (opcional — para emuladores y deploy)
if command -v firebase >/dev/null 2>&1; then
  success "Firebase CLI detectado"
else
  warn "Firebase CLI no encontrado. Instalar con: npm install -g firebase-tools"
fi

# Docker (opcional — para desarrollo en contenedor)
if command -v docker >/dev/null 2>&1; then
  success "Docker detectado"
else
  warn "Docker no encontrado — opcional para desarrollo local"
fi

echo ""

# ----------------------------------------------------------------
# Backend — Entorno virtual Python
# ----------------------------------------------------------------
info "Configurando entorno virtual Python..."

cd "$BACKEND_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
  success "Virtualenv creado en backend/.venv"
else
  success "Virtualenv ya existe en backend/.venv"
fi

# Activar y actualizar pip
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip

# ----------------------------------------------------------------
# Backend — Instalar dependencias
# ----------------------------------------------------------------
info "Instalando dependencias del backend..."
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt
success "Dependencias instaladas"

# ----------------------------------------------------------------
# Backend — Archivo .env
# ----------------------------------------------------------------
if [[ ! -f ".env" ]]; then
  info "Creando backend/.env desde .env.example..."
  cp .env.example .env

  # Generar claves seguras automáticamente si openssl está disponible
  if command -v openssl >/dev/null 2>&1; then
    JWT_KEY=$(openssl rand -hex 32)
    HMAC_KEY=$(openssl rand -hex 32)

    # Reemplazar valores placeholder
    sed -i "s|CAMBIAR-POR-CLAVE-SEGURA-openssl-rand-hex-32|$JWT_KEY|" .env
    sed -i "s|CAMBIAR-POR-OTRA-CLAVE-SEGURA-openssl-rand-hex-32|$HMAC_KEY|" .env

    success "backend/.env creado con claves JWT y HMAC generadas automáticamente"
  else
    warn "openssl no disponible. Editar backend/.env manualmente:"
    warn "  JWT_SECRET_KEY=\$(openssl rand -hex 32)"
    warn "  HMAC_SECRET_KEY=\$(openssl rand -hex 32)"
  fi
else
  success "backend/.env ya existe — no se sobreescribe"
fi

# ----------------------------------------------------------------
# Backend — Verificar credenciales Firebase
# ----------------------------------------------------------------
if [[ ! -f "firebase_credentials.json" ]]; then
  warn "Falta backend/firebase_credentials.json"
  warn "Descargar desde: Firebase Console → Configuración → Cuentas de servicio"
  warn "Guardar como: backend/firebase_credentials.json"
fi

# ----------------------------------------------------------------
# Flutter — Portal Cliente
# ----------------------------------------------------------------
cd "$ROOT_DIR"

if command -v flutter >/dev/null 2>&1 && [[ -d "apps/cliente" ]]; then
  info "Instalando dependencias Flutter — portal cliente..."
  cd apps/cliente
  flutter pub get --suppress-analytics
  success "Flutter pub get completado"

  if [[ ! -f ".dart-defines.json" ]]; then
    info "Creando apps/cliente/.dart-defines.json..."
    cp .dart-defines.example.json .dart-defines.json
    warn "Editar apps/cliente/.dart-defines.json con los valores reales de Firebase"
  fi

  cd "$ROOT_DIR"
fi

# ----------------------------------------------------------------
# Resumen final
# ----------------------------------------------------------------
echo ""
echo "  ✓ Setup completado"
echo "  ==================="
echo ""
echo "  Próximos pasos:"
echo ""
echo "  1. Completar backend/.env:"
echo "     - FIREBASE_PROJECT_ID (ya configurado por defecto)"
echo ""
echo "  2. Descargar firebase_credentials.json:"
echo "     Firebase Console → Configuración → Cuentas de servicio"
echo "     Guardar en: backend/firebase_credentials.json"
echo ""
echo "  3. Iniciar desarrollo:"
echo "     make dev        (backend con hot reload)"
echo "     make emulators  (Firebase Emulator, terminal separada)"
echo ""
echo "  Ver docs/LOCAL_DEVELOPMENT.md para guía completa."
echo ""
