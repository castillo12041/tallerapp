#!/usr/bin/env bash
# ============================================================
# backup_firestore.sh — Export manual de Firestore a Cloud Storage
#
# Uso: bash scripts/backup_firestore.sh
#
# Prerrequisito: gcloud autenticado con permisos de Firestore export
# ============================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-taller-85514}"
BACKUP_BUCKET="${BACKUP_BUCKET:-taller-85514-firestore-backups}"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_PATH="gs://$BACKUP_BUCKET/manual/$DATE"

echo "→ Iniciando export manual de Firestore..."
echo "  Proyecto:  $PROJECT_ID"
echo "  Destino:   $BACKUP_PATH"

gcloud firestore export "$BACKUP_PATH" \
  --project="$PROJECT_ID" \
  --async

echo ""
echo "✓ Export iniciado en background"
echo "  Ver estado: gcloud firestore operations list --project=$PROJECT_ID"
echo "  Ruta:       $BACKUP_PATH"
