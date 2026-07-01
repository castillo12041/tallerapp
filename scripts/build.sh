#!/usr/bin/env bash
# ============================================================
# build.sh — Build de imágenes Docker y apps Flutter
#
# Uso: bash scripts/build.sh [backend|cliente|admin|all]
#      make build
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}→${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
error()   { echo -e "${RED}✗${NC} $1"; exit 1; }

TARGET="${1:-backend}"

build_backend() {
  info "Build Docker — backend..."
  docker build \
    -t tallerapp-backend:latest \
    -t "tallerapp-backend:$(date +%Y%m%d)" \
    "$ROOT_DIR/backend"
  success "Imagen tallerapp-backend:latest lista"
}

build_flutter_cliente() {
  info "Build Flutter Web — portal cliente..."
  local defines_file="$ROOT_DIR/apps/cliente/.dart-defines.json"
  [[ -f "$defines_file" ]] || error "Falta apps/cliente/.dart-defines.json"

  cd "$ROOT_DIR/apps/cliente"
  flutter build web \
    --dart-define-from-file=.dart-defines.json \
    --release \
    --web-renderer canvaskit
  success "Build cliente en: apps/cliente/build/web"
}

build_flutter_admin() {
  info "Build Flutter Web — panel admin..."
  local defines_file="$ROOT_DIR/apps/web_admin/.dart-defines.json"
  [[ -f "$defines_file" ]] || error "Falta apps/web_admin/.dart-defines.json"

  cd "$ROOT_DIR/apps/web_admin"
  flutter build web \
    --dart-define-from-file=.dart-defines.json \
    --release \
    --web-renderer canvaskit
  success "Build admin en: apps/web_admin/build/web"
}

case "$TARGET" in
  backend) build_backend ;;
  cliente) build_flutter_cliente ;;
  admin)   build_flutter_admin ;;
  all)
    build_backend
    build_flutter_cliente
    build_flutter_admin
    ;;
  *)
    echo "Uso: $0 [backend|cliente|admin|all]"
    exit 1
    ;;
esac
