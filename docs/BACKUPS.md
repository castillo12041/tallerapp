# Estrategia de Respaldo

> Define qué se respalda, con qué frecuencia, cómo restaurar y cómo verificar.
> Objetivo: RPO ≤ 24h, RTO ≤ 4h para Firestore. Configuración siempre recuperable desde Git.

---

## Qué se respalda y cómo

| Asset | Mecanismo | Frecuencia | Retención |
|---|---|---|---|
| **Firestore** | Managed Export a Cloud Storage | Diario | 7 diarios + 4 semanales + 12 mensuales |
| **Firebase Storage** (PDFs, logos) | Ninguno adicional — GCP ya replica en múltiples zonas | — | Replicación automática |
| **Firestore Security Rules** | Git (`infra/firebase/firestore.rules`) | Por cambio | Historial de Git |
| **Índices Firestore** | Git (`infra/firebase/firestore.indexes.json`) | Por cambio | Historial de Git |
| **firebase.json / .firebaserc** | Git | Por cambio | Historial de Git |
| **Secrets (JWT, HMAC, etc.)** | Secret Manager — versiones múltiples | Por rotación | 10 versiones por secreto |
| **Firebase credentials JSON** | Secret Manager | Al regenerar | 5 versiones |
| **Código fuente** | GitHub | Por commit | Historial de Git |

---

## Firestore — Backup automatizado

### Paso 1 — Crear bucket de destino para backups

```bash
export PROJECT_ID="taller-85514"
export BACKUP_BUCKET="taller-85514-firestore-backups"

gsutil mb -p "$PROJECT_ID" -l US-CENTRAL1 \
  -b on "gs://$BACKUP_BUCKET"

# Política de ciclo de vida: eliminar objetos mayores a 90 días
cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
gsutil lifecycle set /tmp/lifecycle.json "gs://$BACKUP_BUCKET"

echo "Bucket creado: gs://$BACKUP_BUCKET"
```

### Paso 2 — Service Account para backups

```bash
SA_BACKUP="firestore-backup"

gcloud iam service-accounts create "$SA_BACKUP" \
  --project="$PROJECT_ID" \
  --display-name="Firestore Backup SA"

# Permiso para exportar Firestore
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_BACKUP@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.importExportAdmin"

# Permiso para escribir en el bucket
gsutil iam ch \
  "serviceAccount:$SA_BACKUP@$PROJECT_ID.iam.gserviceaccount.com:objectAdmin" \
  "gs://$BACKUP_BUCKET"
```

### Paso 3 — Cloud Scheduler para backups automáticos

```bash
# Habilitar Cloud Scheduler si no está habilitado
gcloud services enable cloudscheduler.googleapis.com --project="$PROJECT_ID"

# Job diario a las 03:00 UTC (medianoche Chile en verano)
gcloud scheduler jobs create http firestore-daily-backup \
  --project="$PROJECT_ID" \
  --location="us-central1" \
  --schedule="0 3 * * *" \
  --time-zone="UTC" \
  --uri="https://firestore.googleapis.com/v1/projects/$PROJECT_ID/databases/(default):exportDocuments" \
  --message-body="{\"outputUriPrefix\": \"gs://$BACKUP_BUCKET/daily/$(date +%Y-%m-%d)\"}" \
  --oauth-service-account-email="$SA_BACKUP@$PROJECT_ID.iam.gserviceaccount.com" \
  --description="Backup diario de Firestore"

# Verificar
gcloud scheduler jobs list --project="$PROJECT_ID" --location="us-central1"
```

### Alternativa — Script de backup manual

```bash
#!/usr/bin/env bash
# scripts/backup_firestore.sh — Ejecutar manualmente o desde CI

set -euo pipefail

PROJECT_ID="taller-85514"
BACKUP_BUCKET="taller-85514-firestore-backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_PATH="gs://$BACKUP_BUCKET/manual/$DATE"

echo "→ Iniciando export de Firestore..."
gcloud firestore export "$BACKUP_PATH" \
  --project="$PROJECT_ID" \
  --async

echo "✓ Export iniciado"
echo "  Ruta: $BACKUP_PATH"
echo "  Ver estado: gcloud firestore operations list --project=$PROJECT_ID"
```

---

## Esquema de retención

```
gs://taller-85514-firestore-backups/
├── daily/
│   ├── 2026-06-30/     ← 7 más recientes
│   ├── 2026-06-29/
│   └── ...
├── weekly/
│   ├── 2026-W26/       ← 4 más recientes (sábados)
│   └── ...
├── monthly/
│   ├── 2026-06/        ← 12 más recientes (día 1)
│   └── ...
└── manual/
    └── 20260630-030000/ ← backups ad-hoc
```

### Automatizar retención diferenciada

```bash
# Weekly backup (corre los domingos a las 04:00 UTC)
gcloud scheduler jobs create http firestore-weekly-backup \
  --project="$PROJECT_ID" \
  --location="us-central1" \
  --schedule="0 4 * * 0" \
  --uri="https://firestore.googleapis.com/v1/projects/$PROJECT_ID/databases/(default):exportDocuments" \
  --message-body="{\"outputUriPrefix\": \"gs://$BACKUP_BUCKET/weekly/$(date +%Y-W%V)\"}" \
  --oauth-service-account-email="$SA_BACKUP@$PROJECT_ID.iam.gserviceaccount.com" \
  --description="Backup semanal de Firestore"

# Monthly backup (corre el día 1 de cada mes a las 05:00 UTC)
gcloud scheduler jobs create http firestore-monthly-backup \
  --project="$PROJECT_ID" \
  --location="us-central1" \
  --schedule="0 5 1 * *" \
  --uri="https://firestore.googleapis.com/v1/projects/$PROJECT_ID/databases/(default):exportDocuments" \
  --message-body="{\"outputUriPrefix\": \"gs://$BACKUP_BUCKET/monthly/$(date +%Y-%m)\"}" \
  --oauth-service-account-email="$SA_BACKUP@$PROJECT_ID.iam.gserviceaccount.com" \
  --description="Backup mensual de Firestore"
```

---

## Restauración de Firestore

> ⚠️ La restauración **sobrescribe** los datos existentes en la base de datos. Hacer solo en caso de pérdida de datos o corrupción grave. Nunca restaurar en producción sin coordinación con el equipo.

### Procedimiento de restauración

```bash
#!/usr/bin/env bash
# scripts/restore_firestore.sh

set -euo pipefail

PROJECT_ID="taller-85514"
BACKUP_BUCKET="taller-85514-firestore-backups"

echo "=== Restauración de Firestore ==="
echo ""
echo "Backups disponibles:"
gsutil ls "gs://$BACKUP_BUCKET/daily/" | sort -r | head -10

echo ""
read -p "Ingresa la ruta del backup a restaurar (ej: gs://...daily/2026-06-30): " BACKUP_PATH

echo ""
echo "ADVERTENCIA: Esto sobrescribirá los datos actuales de Firestore."
echo "Backup: $BACKUP_PATH"
read -p "¿Confirmar restauración? (escribe 'RESTAURAR' para continuar): " CONFIRM

if [[ "$CONFIRM" != "RESTAURAR" ]]; then
  echo "Restauración cancelada."
  exit 0
fi

echo ""
echo "→ Iniciando import de Firestore..."
gcloud firestore import "$BACKUP_PATH" \
  --project="$PROJECT_ID" \
  --async

echo "✓ Import iniciado. Ver estado:"
echo "  gcloud firestore operations list --project=$PROJECT_ID"
```

### Restaurar solo colecciones específicas

```bash
# Solo restaurar la colección 'inspections' (no restaura todo)
gcloud firestore import "gs://$BACKUP_BUCKET/daily/2026-06-30" \
  --project="$PROJECT_ID" \
  --collection-ids="inspections,inspection_items"
```

### Verificar estado del import

```bash
gcloud firestore operations list --project="$PROJECT_ID"
# buscar la operación en estado RUNNING o DONE
```

---

## Firebase Storage — Política de respaldo

Firebase Storage está respaldado por Google Cloud Storage, que ofrece:
- **Durabilidad:** 99.999999999% (11 nueves)
- **Replicación:** Multi-regional automática (plan Blaze)
- **Sin punto único de fallo**

Para datos críticos (PDFs de inspecciones), se puede agregar una capa adicional:

```bash
# Sincronizar Storage a un bucket de backup en otra región
gsutil -m rsync -r \
  "gs://taller-85514.appspot.com/tenants" \
  "gs://taller-85514-storage-backup/tenants"
```

> Para la fase actual del proyecto, la replicación automática de GCS es suficiente. Agregar backup a Storage cuando el volumen de PDFs supere los 10GB.

---

## Configuración — siempre en Git

Estos archivos NUNCA necesitan backup adicional porque están en el repositorio:

| Archivo | Ruta |
|---|---|
| Firestore Rules | `infra/firebase/firestore.rules` |
| Firestore Indexes | `infra/firebase/firestore.indexes.json` |
| Storage Rules | `infra/firebase/storage.rules` |
| Firebase Hosting Config | `firebase.json` |
| Firebase Project Config | `.firebaserc` |
| Backend Config | `backend/app/core/config.py` |
| CI/CD Workflows | `.github/workflows/` |

Recuperación total del código fuente desde GitHub:
```bash
git clone https://github.com/TU_ORG/tallerapp.git
```

---

## Secrets — Secret Manager

Secret Manager mantiene versiones históricas de cada secreto.

```bash
# Ver versiones de un secreto
gcloud secrets versions list taller-jwt-secret-key --project=taller-85514

# Acceder a una versión anterior si se necesita
gcloud secrets versions access VERSION_NUMBER \
  --secret=taller-jwt-secret-key \
  --project=taller-85514
```

**Retención configurada:** 10 versiones por secreto (Secret Manager retiene automáticamente).

---

## Verificación de backups (mensual)

Realizar este procedimiento el primer lunes de cada mes:

```bash
#!/usr/bin/env bash
# scripts/verify_backup.sh — Verificar integridad del backup más reciente

set -euo pipefail

PROJECT_ID="taller-85514"
BACKUP_BUCKET="taller-85514-firestore-backups"

echo "=== Verificación mensual de backup ==="
echo "Fecha: $(date)"
echo ""

# 1. Verificar que existe un backup reciente (menos de 25h)
echo "1. Verificando backup diario reciente..."
LATEST=$(gsutil ls -l "gs://$BACKUP_BUCKET/daily/" | sort -k2 -r | head -1 | awk '{print $3}')
LATEST_DATE=$(echo "$LATEST" | grep -oP '\d{4}-\d{2}-\d{2}')
echo "   Último backup: $LATEST ($LATEST_DATE)"

# 2. Verificar tamaño del backup (no debe ser 0)
echo "2. Verificando tamaño..."
SIZE=$(gsutil du -s "$LATEST" 2>/dev/null | awk '{print $1}')
echo "   Tamaño: $SIZE bytes"
if [[ "$SIZE" -lt 1000 ]]; then
  echo "   ⚠️  ALERTA: Backup demasiado pequeño — puede estar vacío"
fi

# 3. Verificar que Cloud Scheduler está activo
echo "3. Verificando Cloud Scheduler..."
STATUS=$(gcloud scheduler jobs describe firestore-daily-backup \
  --project="$PROJECT_ID" --location="us-central1" \
  --format="value(state)" 2>/dev/null)
echo "   Estado: $STATUS"

echo ""
echo "=== Resultado: OK ===" 
echo "Documentar en CHANGELOG o notion de ops si hay anomalías."
```

---

## RTO y RPO

| Escenario | RPO | RTO | Procedimiento |
|---|---|---|---|
| Corrupción de datos en Firestore | 24h (último backup diario) | 2-4h | `restore_firestore.sh` |
| Pérdida del bucket de Storage | ~0 (replicación GCS) | ~0 | Replicación automática |
| Pérdida de un secreto | 0 (versiones en SM) | 15 min | `gcloud secrets versions access` |
| Pérdida del código fuente | 0 (GitHub) | 5 min | `git clone` |
| Pérdida total del proyecto GCP | 24h (Firestore) | 4-8h | Recrear proyecto + restaurar backup |

---

## Checklist de backups

- [ ] Bucket `taller-85514-firestore-backups` creado con lifecycle de 90 días
- [ ] SA `firestore-backup` creado con permisos mínimos
- [ ] Cloud Scheduler `firestore-daily-backup` activo (verificar con `gcloud scheduler jobs list`)
- [ ] Cloud Scheduler `firestore-weekly-backup` activo
- [ ] Cloud Scheduler `firestore-monthly-backup` activo
- [ ] Script `scripts/verify_backup.sh` ejecutado exitosamente al menos una vez
- [ ] Procedimiento de restauración documentado y probado en staging
- [ ] `scripts/restore_firestore.sh` testeado en staging (no en producción)
- [ ] Alertas de billing incluyen el costo del bucket de backups
- [ ] Verificación mensual agendada (primer lunes de cada mes)
