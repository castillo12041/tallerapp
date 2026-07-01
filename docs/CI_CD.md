# CI/CD — Pipeline de Integración y Despliegue

> Documentación del pipeline automatizado con GitHub Actions.
> Prerrequisito: completar [GOOGLE_CLOUD.md](GOOGLE_CLOUD.md) antes de activar los deploys.

---

## Arquitectura del Pipeline

```
Push / PR
    │
    ▼
┌─────────────────────────────────────────┐
│  CI (.github/workflows/ci.yml)          │
│                                         │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ lint-backend │  │  test-backend   │  │  ← paralelo
│  │ ruff + mypy  │  │  pytest ≥ 80%   │  │
│  └──────────────┘  └─────────────────┘  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   analyze-flutter-cliente       │    │
│  │   flutter analyze + dart format │    │
│  └─────────────────────────────────┘    │
└──────────────────┬──────────────────────┘
                   │ (solo en push a main)
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌──────────────────┐
│ Deploy Backend│    │  Deploy Hosting  │
│ (Cloud Run)   │    │  (Firebase)      │
│               │    │                  │
│ 1. Build img  │    │ 1. flutter build │
│ 2. Push AR    │    │    web-cliente   │
│ 3. gcloud run │    │ 2. firebase      │
│    deploy     │    │    deploy        │
└───────────────┘    └──────────────────┘
```

---

## Workflows

| Archivo | Trigger | Propósito |
|---|---|---|
| `ci.yml` | Push a main/develop, PR a main | Lint + tests + análisis Flutter |
| `deploy-backend.yml` | Push a main (paths: backend/**) + manual | Deploy a Cloud Run |
| `deploy-hosting.yml` | Push a main (paths: apps/**) + manual | Deploy a Firebase Hosting |

---

## Configuración inicial (hacer UNA VEZ)

### 1. Crear repositorio en GitHub

```bash
git remote add origin https://github.com/TU_ORG/tallerapp.git
git push -u origin main
```

### 2. Configurar Workload Identity Federation en GCP

Workload Identity Federation permite que GitHub Actions se autentique en GCP **sin service account keys**. Es más seguro porque no hay credenciales de larga duración.

```bash
# Variables
PROJECT_ID="taller-85514"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"
SA_NAME="github-deploy"
GITHUB_ORG="TU_ORG"     # Tu organización o usuario de GitHub
GITHUB_REPO="tallerapp"  # Nombre del repositorio

# 1. Crear Workload Identity Pool
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 2. Crear Provider para GitHub
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 3. Crear Service Account para deploys
gcloud iam service-accounts create "$SA_NAME" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions Deploy"

# 4. Dar permisos al SA
for ROLE in \
  "roles/run.admin" \
  "roles/artifactregistry.writer" \
  "roles/secretmanager.secretAccessor" \
  "roles/storage.admin" \
  "roles/iam.serviceAccountUser"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE"
done

# 5. Vincular GitHub repo al SA via WIF
gcloud iam service-accounts add-iam-policy-binding \
  "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$GITHUB_ORG/$GITHUB_REPO"

# 6. Obtener el Provider URI (copiar en GitHub Secrets)
echo "WIF Provider URI:"
echo "projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/providers/$PROVIDER_NAME"
```

### 3. Crear Artifact Registry para imágenes Docker

```bash
gcloud artifacts repositories create tallerapp \
  --repository-format=docker \
  --location=us-central1 \
  --project="$PROJECT_ID" \
  --description="Taller Inspección Docker images"
```

### 4. Crear Service en Cloud Run (primera vez)

El workflow hace `gcloud run deploy` que crea el servicio si no existe. Pero para control inicial:

```bash
gcloud run services create tallerapp-api \
  --region=us-central1 \
  --project="$PROJECT_ID" \
  --platform=managed \
  --no-traffic
```

---

## GitHub Variables y Secrets

Configurar en: `GitHub → Repository → Settings → Secrets and variables → Actions`

### Variables (no sensibles — visibles en logs)

| Variable | Valor de ejemplo | Descripción |
|---|---|---|
| `GCP_PROJECT_ID` | `taller-85514` | ID del proyecto GCP |
| `GCP_REGION` | `us-central1` | Región de Cloud Run |
| `ARTIFACT_REGISTRY_LOCATION` | `us-central1` | Región de Artifact Registry |
| `CLOUD_RUN_SERVICE` | `tallerapp-api` | Nombre del servicio Cloud Run |
| `PUBLIC_BASE_URL` | `https://tallerinspeccion.tapsolutions.cl` | URL base para tokens públicos |
| `ALLOWED_ORIGINS` | `https://tallerinspeccion.tapsolutions.cl,...` | CORS origins (separados por coma) |
| `API_BASE_URL_PROD` | `https://api.tallerinspeccion.tapsolutions.cl` | URL API para Flutter apps |
| `FIREBASE_PROJECT_ID` | `taller-85514` | ID proyecto Firebase |

### Secrets (sensibles — ocultos en logs)

| Secret | Descripción | Cómo obtener |
|---|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | URI del WIF Provider | Paso 6 del setup WIF |
| `GCP_SERVICE_ACCOUNT` | Email del SA | `$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com` |
| `FIREBASE_API_KEY_WEB` | API Key Firebase Web | Firebase Console → Configuración → Web |
| `FIREBASE_MESSAGING_SENDER_ID` | FCM Sender ID | Firebase Console → Configuración → Web |
| `FIREBASE_APP_ID_CLIENTE` | App ID del portal cliente | Firebase Console → Configuración → Tus apps |
| `FIREBASE_APP_ID_ADMIN` | App ID del panel admin | Firebase Console → Configuración → Tus apps |
| `FIREBASE_MEASUREMENT_ID_CLIENTE` | Analytics Measurement ID | Firebase Console → Analytics |

---

## Secrets en Google Secret Manager

El backend en Cloud Run usa secretos desde Secret Manager (inyectados como env vars y archivos).

### Crear los secretos

```bash
PROJECT_ID="taller-85514"

# JWT Secret Key
JWT_KEY=$(openssl rand -hex 32)
echo -n "$JWT_KEY" | \
  gcloud secrets create taller-jwt-secret-key \
    --project="$PROJECT_ID" \
    --data-file=-

# HMAC Secret Key
HMAC_KEY=$(openssl rand -hex 32)
echo -n "$HMAC_KEY" | \
  gcloud secrets create taller-hmac-secret-key \
    --project="$PROJECT_ID" \
    --data-file=-

# Firebase Credentials JSON
gcloud secrets create taller-firebase-credentials \
  --project="$PROJECT_ID" \
  --data-file=backend/firebase_credentials.json
```

> Guardar `$JWT_KEY` y `$HMAC_KEY` en un gestor de contraseñas seguro. Son irrecuperables desde Secret Manager.

### Verificar acceso del SA a los secretos

```bash
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

for SECRET in taller-jwt-secret-key taller-hmac-secret-key taller-firebase-credentials; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --project="$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
done
```

---

## Flujo de trabajo con el pipeline

### Desarrollo normal (feature branch)

```
feature/nueva-funcionalidad
    │
    ├── git push → CI corre (lint + test + flutter analyze)
    │             No se despliega nada
    │
    └── PR a main → CI corre de nuevo
                    Code review
                    Merge → Deploy automático
```

### Deploy manual de emergencia

```bash
# Desde GitHub UI:
# Actions → Deploy Backend → Run workflow → main → Run

# O con GitHub CLI:
gh workflow run deploy-backend.yml --ref main
gh workflow run deploy-hosting.yml --ref main --field target=web-cliente
```

### Rollback

```bash
# Listar revisiones del servicio
gcloud run revisions list \
  --service=tallerapp-api \
  --region=us-central1 \
  --project=taller-85514

# Enviar 100% de tráfico a una revisión anterior
gcloud run services update-traffic tallerapp-api \
  --region=us-central1 \
  --project=taller-85514 \
  --to-revisions=tallerapp-api-REVISION_NAME=100
```

---

## Cache y performance

### Tiempos de CI estimados (con cache caliente)

| Job | Sin cache | Con cache |
|---|---|---|
| `lint-backend` | ~2 min | ~40 seg |
| `test-backend` | ~3 min | ~1 min |
| `analyze-flutter-cliente` | ~5 min | ~2 min |
| `deploy-backend` (build Docker) | ~8 min | ~3 min (layers cacheadas) |
| `deploy-hosting` (build Flutter) | ~6 min | ~3 min |

**Total pipeline completo: ~10-12 min con cache**

### Cache de Docker layers

Los builds de Docker usan cache de Artifact Registry (`type=registry`):
- La capa de dependencias Python (pip install) se cachea si `requirements.prod.txt` no cambió
- Solo se reconstruye la capa de código fuente en cada commit
- ~70% de ahorro en tiempo de build habitual

---

## Ambientes

| Ambiente | Branch | Backend | Frontend |
|---|---|---|---|
| Development | `feature/*` | `localhost:8000` | `localhost:57627` |
| Staging | `develop` | (configurar) | (configurar) |
| Production | `main` | Cloud Run | Firebase Hosting |

> El ambiente de staging se puede agregar creando un segundo proyecto Firebase (`taller-85514-staging`) y configurando un segundo conjunto de variables en GitHub.

---

## Troubleshooting CI/CD

### `Error: google-github-actions/auth failed`

Verificar:
1. `GCP_WORKLOAD_IDENTITY_PROVIDER` es el URI completo del provider (no el pool)
2. El SA tiene el binding correcto con el repositorio GitHub
3. El `repository` en el WIF provider attribute mapping coincide con `ORG/REPO`

```bash
# Verificar el binding
gcloud iam service-accounts get-iam-policy \
  "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --project="$PROJECT_ID"
```

### `PERMISSION_DENIED: Artifact Registry`

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### `Cloud Run deploy: secret not found`

```bash
# Verificar que el secreto existe
gcloud secrets list --project="$PROJECT_ID" | grep taller-

# Verificar acceso del SA
gcloud secrets get-iam-policy taller-jwt-secret-key --project="$PROJECT_ID"
```

### `Flutter build: dart-define not provided`

En el workflow `deploy-hosting.yml`, verificar que todos los GitHub Secrets/Variables están configurados. Los dart-defines son pasados como `--dart-define=KEY=VALUE` en el step de build.

### Tests fallan en CI pero pasan local

1. Verificar que `backend/requirements-dev.txt` está actualizado
2. Los tests usan mocks de Firebase — no necesitan credenciales reales en CI
3. Revisar si hay imports de módulos no incluidos en `requirements.txt` o `requirements-dev.txt`

---

## Próximos pasos del pipeline

- **Fase 20 (CI/CD completo):** Agregar notificaciones Slack/email en deploy, staging automático, tests E2E en CI, performance tests con k6
- **App Mobile:** Agregar jobs de build APK/IPA con `flutter build apk` y publicación a Play Store / TestFlight
