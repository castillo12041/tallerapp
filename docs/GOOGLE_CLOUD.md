# Google Cloud Platform — Configuración Completa

> Guía paso a paso para configurar GCP para Taller Inspección.
> Ejecutar en orden. Requiere: `gcloud CLI` instalado y autenticado.

---

## Variables de referencia

Usar estas variables en todos los comandos de esta guía:

```bash
export PROJECT_ID="taller-85514"
export REGION="us-central1"          # Región principal de Cloud Run
export AR_LOCATION="us-central1"     # Artifact Registry
export BILLING_ACCOUNT="XXXX-XXXX-XXXX"  # ID de cuenta de facturación
```

Para obtener el Billing Account ID:
```bash
gcloud billing accounts list
```

---

## Paso 1 — Proyecto GCP

### 1.1 Crear proyecto (si no existe)

```bash
gcloud projects create "$PROJECT_ID" \
  --name="Taller Inspección" \
  --set-as-default

# Vincular a cuenta de facturación
gcloud billing projects link "$PROJECT_ID" \
  --billing-account="$BILLING_ACCOUNT"
```

### 1.2 Verificar configuración activa

```bash
gcloud config set project "$PROJECT_ID"
gcloud config list
```

---

## Paso 2 — Habilitar APIs

```bash
gcloud services enable \
  firestore.googleapis.com \
  firebase.googleapis.com \
  storage.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  --project="$PROJECT_ID"
```

Verificar:
```bash
gcloud services list --enabled --project="$PROJECT_ID" --filter="name:run.googleapis.com"
```

---

## Paso 3 — Service Accounts

Se crean dos Service Accounts con permisos mínimos.

### 3.1 SA del backend en Cloud Run

Esta SA corre dentro del contenedor de Cloud Run.
Tiene acceso a Firebase/Firestore y Secret Manager.

```bash
SA_BACKEND="tallerapp-backend"

gcloud iam service-accounts create "$SA_BACKEND" \
  --project="$PROJECT_ID" \
  --display-name="Taller App — Backend Runtime" \
  --description="Service Account para el servicio Cloud Run del backend FastAPI"

# Permisos requeridos
for ROLE in \
  "roles/datastore.user" \
  "roles/firebase.sdkAdminServiceAgent" \
  "roles/storage.objectAdmin" \
  "roles/secretmanager.secretAccessor" \
  "roles/cloudtrace.agent" \
  "roles/logging.logWriter"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_BACKEND@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE"
done

echo "SA Backend: $SA_BACKEND@$PROJECT_ID.iam.gserviceaccount.com"
```

### 3.2 SA para GitHub Actions (deploys)

Esta SA NO corre en producción. Solo la usa el pipeline CI/CD.

```bash
SA_DEPLOY="github-deploy"

gcloud iam service-accounts create "$SA_DEPLOY" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions — Deploy" \
  --description="Service Account para CI/CD. Permisos de despliegue únicamente."

for ROLE in \
  "roles/run.admin" \
  "roles/artifactregistry.writer" \
  "roles/secretmanager.secretAccessor" \
  "roles/storage.objectViewer" \
  "roles/iam.serviceAccountUser"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_DEPLOY@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE"
done
```

### 3.3 Workload Identity Federation para GitHub Actions

Ver `docs/CI_CD.md` → sección "Configuración inicial GCP" para los comandos completos.
Este paso vincula el SA `github-deploy` con el repositorio de GitHub sin usar claves.

---

## Paso 4 — Artifact Registry

Repositorio Docker para las imágenes del backend.

```bash
gcloud artifacts repositories create tallerapp \
  --repository-format=docker \
  --location="$AR_LOCATION" \
  --project="$PROJECT_ID" \
  --description="Imágenes Docker — Taller Inspección"

# Verificar
gcloud artifacts repositories list --project="$PROJECT_ID"

# URL del repositorio (usar en workflows de CI/CD)
echo "$AR_LOCATION-docker.pkg.dev/$PROJECT_ID/tallerapp/backend"
```

---

## Paso 5 — Secret Manager

Todos los secretos de producción viven aquí.

### 5.1 Crear secretos

```bash
# JWT Secret Key (para access tokens internos)
JWT_KEY=$(openssl rand -hex 32)
echo -n "$JWT_KEY" | gcloud secrets create taller-jwt-secret-key \
  --project="$PROJECT_ID" \
  --data-file=- \
  --replication-policy=automatic

# HMAC Secret Key (para tokens QR y presupuestos públicos)
HMAC_KEY=$(openssl rand -hex 32)
echo -n "$HMAC_KEY" | gcloud secrets create taller-hmac-secret-key \
  --project="$PROJECT_ID" \
  --data-file=- \
  --replication-policy=automatic

# Firebase Service Account JSON
# (descargar desde Firebase Console → Cuentas de servicio → Generar clave)
gcloud secrets create taller-firebase-credentials \
  --project="$PROJECT_ID" \
  --data-file=backend/firebase_credentials.json \
  --replication-policy=automatic

# SendGrid API Key (Fase 15 — notificaciones email)
# echo -n "SG.xxxxx" | gcloud secrets create taller-sendgrid-api-key \
#   --project="$PROJECT_ID" --data-file=- --replication-policy=automatic

echo "✓ Secretos creados"
echo "  GUARDAR JWT_KEY y HMAC_KEY en un gestor de contraseñas — son irrecuperables desde GCP."
```

> ⚠️ Guardar `$JWT_KEY` y `$HMAC_KEY` en un lugar seguro (1Password, Bitwarden, etc.). Son irrecuperables si se pierden. Rotar ambas keys invalida todos los tokens activos.

### 5.2 Verificar acceso del SA backend a los secretos

```bash
for SECRET in taller-jwt-secret-key taller-hmac-secret-key taller-firebase-credentials; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --project="$PROJECT_ID" \
    --member="serviceAccount:$SA_BACKEND@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 5.3 Rotar secretos

Para rotar un secreto sin downtime:

```bash
# Agregar nueva versión
NEW_JWT=$(openssl rand -hex 32)
echo -n "$NEW_JWT" | gcloud secrets versions add taller-jwt-secret-key \
  --project="$PROJECT_ID" \
  --data-file=-

# Cloud Run automáticamente tomará :latest en el próximo deploy.
# Los tokens firmados con la versión anterior quedarán inválidos → logout masivo.
# Planificar ventana de mantenimiento para rotaciones JWT.
```

---

## Paso 6 — Cloud Run

### 6.1 Configuración del servicio

El primer deploy se hace via GitHub Actions. Para configuración manual o ajustes:

```bash
SA_EMAIL="$SA_BACKEND@$PROJECT_ID.iam.gserviceaccount.com"

gcloud run services update tallerapp-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --service-account="$SA_EMAIL" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=60s \
  --concurrency=80 \
  --port=8000
```

### 6.2 Configurar dominio personalizado

```bash
# Mapear api.tallerinspeccion.tapsolutions.cl → Cloud Run
gcloud run domain-mappings create \
  --service=tallerapp-api \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region="$REGION" \
  --project="$PROJECT_ID"

# GCP dará registros DNS a agregar en tu proveedor de dominio
gcloud run domain-mappings describe \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region="$REGION" \
  --project="$PROJECT_ID"
```

### 6.3 Variables de entorno en Cloud Run

Configuradas automáticamente por el workflow `deploy-backend.yml`.
Para actualizar manualmente:

```bash
gcloud run services update tallerapp-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --set-env-vars "ALLOWED_ORIGINS=https://tallerinspeccion.tapsolutions.cl,https://admin.tallerinspeccion.tapsolutions.cl,https://cliente.tallerinspeccion.tapsolutions.cl" \
  --set-env-vars "PUBLIC_BASE_URL=https://tallerinspeccion.tapsolutions.cl"
```

---

## Paso 7 — Presupuestos y Alertas de Costos

Fundamental para SaaS — evita facturas inesperadas.

```bash
# Alertar al 50%, 90% y 100% de los umbrales
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="Taller App — Alerta $100 USD" \
  --budget-amount=100USD \
  --threshold-rule=percent=0.5,basis=CURRENT_SPEND \
  --threshold-rule=percent=0.9,basis=CURRENT_SPEND \
  --threshold-rule=percent=1.0,basis=CURRENT_SPEND \
  --filter-projects="projects/$PROJECT_ID" \
  --notifications-rule-pubsub-topic=projects/$PROJECT_ID/topics/billing-alerts

# Crear un segundo presupuesto para alerta crítica a $500 USD
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="Taller App — CRÍTICO $500 USD" \
  --budget-amount=500USD \
  --threshold-rule=percent=1.0,basis=CURRENT_SPEND \
  --filter-projects="projects/$PROJECT_ID"
```

**Costos estimados del proyecto en producción (baja escala):**

| Servicio | Uso estimado | Costo/mes |
|---|---|---|
| Cloud Run | 100K requests/mes, 512MB | ~$2-5 |
| Artifact Registry | 5 imágenes, ~1GB | ~$0.10 |
| Secret Manager | 5 secretos, 1K accesos | ~$0.06 |
| Firestore | 50K reads, 10K writes | ~$0.05 |
| Firebase Storage | 5GB | ~$0.13 |
| Firebase Hosting | 10GB transfer | ~$0 (plan gratuito) |
| **Total estimado** | | **~$3-8 USD/mes** |

---

## Paso 8 — Logging y Auditoría

### 8.1 Habilitar Data Access Audit Logs

```bash
cat > /tmp/iam_policy_delta.json << 'EOF'
{
  "auditConfigs": [
    {
      "service": "firestore.googleapis.com",
      "auditLogConfigs": [
        {"logType": "DATA_READ"},
        {"logType": "DATA_WRITE"}
      ]
    },
    {
      "service": "secretmanager.googleapis.com",
      "auditLogConfigs": [
        {"logType": "DATA_READ"},
        {"logType": "DATA_WRITE"},
        {"logType": "ADMIN_READ"}
      ]
    },
    {
      "service": "run.googleapis.com",
      "auditLogConfigs": [
        {"logType": "ADMIN_READ"},
        {"logType": "DATA_WRITE"}
      ]
    }
  ]
}
EOF

gcloud projects set-iam-policy "$PROJECT_ID" /tmp/iam_policy_delta.json
```

### 8.2 Exportar logs a BigQuery (opcional para analytics)

```bash
gcloud logging sinks create taller-audit-sink \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/audit_logs \
  --log-filter='resource.type="cloud_run_revision" OR resource.type="audited_resource"' \
  --project="$PROJECT_ID"
```

### 8.3 Log-based metric: Errores del backend

```bash
gcloud logging metrics create backend-5xx-errors \
  --description="Errores HTTP 5xx del backend FastAPI" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="tallerapp-api" AND httpRequest.status>=500' \
  --project="$PROJECT_ID"
```

---

## Paso 9 — Monitoring y Alertas

### 9.1 Uptime check (health check continuo)

```bash
# Crear uptime check para el health endpoint
gcloud monitoring uptime-checks create http tallerapp-health \
  --project="$PROJECT_ID" \
  --display-name="Taller App API Health" \
  --uri="https://api.tallerinspeccion.tapsolutions.cl/api/v1/health" \
  --period=60 \
  --timeout=10
```

### 9.2 Política de alertas — Errores 5xx

Configurar en Cloud Console → Monitoring → Alerting → Create Policy:

```
Condición: backend-5xx-errors > 10 en 5 minutos
Canal: Email a peladocastillo@gmail.com
Severidad: Critical
```

### 9.3 Política de alertas — Latencia alta

```
Condición: Cloud Run request latency p95 > 2000ms en 10 minutos
Canal: Email
Severidad: Warning
```

---

## Paso 10 — Verificación completa

```bash
echo "=== Verificación GCP ==="

# APIs habilitadas
echo "APIs habilitadas:"
gcloud services list --enabled --project="$PROJECT_ID" \
  --filter="name:(run.googleapis.com OR secretmanager.googleapis.com OR artifactregistry.googleapis.com)" \
  --format="table(name)"

# Service Accounts
echo "Service Accounts:"
gcloud iam service-accounts list --project="$PROJECT_ID"

# Secretos
echo "Secretos:"
gcloud secrets list --project="$PROJECT_ID"

# Artifact Registry
echo "Repositorios:"
gcloud artifacts repositories list --project="$PROJECT_ID"

# Cloud Run
echo "Cloud Run services:"
gcloud run services list --project="$PROJECT_ID"
```

---

## Referencia de costos por característica

| Feature activada | Impacto en costo |
|---|---|
| Cloud Run con min-instances=1 | +$10-15/mes (evita cold starts) |
| Cloud Run con min-instances=0 | Gratis cuando sin tráfico, cold start ~2s |
| Logging de Data Access en Firestore | Puede aumentar costos de logging significativamente |
| Cloud Armor (WAF) | ~$5/mes + $0.75/M requests |
| Cloud CDN | ~$0.01/GB de salida |

> Para una etapa inicial de SaaS, recomendamos `min-instances=0` y sin logging de Data Access en Firestore. Activar cuando el proyecto tenga usuarios reales.
