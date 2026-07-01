# Despliegue — Proceso Completo

> Manual de despliegue para producción.
> Distingue entre: primer despliegue (setup completo) y despliegues subsiguientes (automáticos vía CI/CD).

---

## Tipos de despliegue

| Tipo | Cuándo | Cómo |
|---|---|---|
| **Primer despliegue** | Una sola vez al iniciar producción | Seguir esta guía completa |
| **Deploy automático** | En cada merge a `main` | GitHub Actions (automático) |
| **Deploy manual** | Emergencias o fixes urgentes | `gh workflow run` o gcloud CLI |
| **Rollback** | Si un deploy rompe algo | Cloud Run traffic splitting |

---

## Prerrequisitos

Completar en orden antes del primer despliegue:

- [ ] `docs/SETUP.md` — entorno local configurado
- [ ] `docs/GOOGLE_CLOUD.md` — GCP: proyecto, service accounts, secretos, Artifact Registry
- [ ] `docs/FIREBASE.md` — Firebase: Auth, Firestore, Storage, Hosting
- [ ] `docs/CI_CD.md` → sección "Configuración inicial GCP" — Workload Identity Federation
- [ ] GitHub Variables y Secrets configurados (ver `docs/CI_CD.md`)
- [ ] Tests pasando localmente: `make test`

---

## Primer despliegue

### Fase A — Preparación de secretos en Secret Manager

```bash
export PROJECT_ID="taller-85514"

# 1. Generar y almacenar JWT Key
JWT_KEY=$(openssl rand -hex 32)
echo -n "$JWT_KEY" | gcloud secrets create taller-jwt-secret-key \
  --project="$PROJECT_ID" --data-file=- --replication-policy=automatic

# 2. Generar y almacenar HMAC Key
HMAC_KEY=$(openssl rand -hex 32)
echo -n "$HMAC_KEY" | gcloud secrets create taller-hmac-secret-key \
  --project="$PROJECT_ID" --data-file=- --replication-policy=automatic

# 3. Almacenar Firebase credentials
gcloud secrets create taller-firebase-credentials \
  --project="$PROJECT_ID" \
  --data-file=backend/firebase_credentials.json \
  --replication-policy=automatic

echo "✓ Secretos en Secret Manager creados"
echo "GUARDAR estos valores:"
echo "  JWT_KEY:  $JWT_KEY"
echo "  HMAC_KEY: $HMAC_KEY"
```

### Fase B — Primer deploy del backend (manual)

El primer deploy se hace manualmente para validar la configuración.

```bash
export REGION="us-central1"
export AR_LOCATION="us-central1"
export SA_BACKEND="tallerapp-backend"
export IMAGE="$AR_LOCATION-docker.pkg.dev/$PROJECT_ID/tallerapp/backend"

# Construir imagen Docker
cd backend
docker build -t "$IMAGE:initial" -t "$IMAGE:latest" .

# Autenticar Docker con Artifact Registry
gcloud auth configure-docker "$AR_LOCATION-docker.pkg.dev"

# Push de la imagen
docker push "$IMAGE:initial"
docker push "$IMAGE:latest"

# Primer deploy a Cloud Run
gcloud run deploy tallerapp-api \
  --image "$IMAGE:initial" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --platform=managed \
  --allow-unauthenticated \
  --service-account="$SA_BACKEND@$PROJECT_ID.iam.gserviceaccount.com" \
  --port=8000 \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=60s \
  --concurrency=80 \
  --set-env-vars="ENVIRONMENT=production" \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID" \
  --set-env-vars="FIREBASE_PROJECT_ID=$PROJECT_ID" \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=$PROJECT_ID.appspot.com" \
  --set-env-vars="FIREBASE_CREDENTIALS_PATH=/secrets/firebase_credentials.json" \
  --set-env-vars="PUBLIC_BASE_URL=https://tallerinspeccion.tapsolutions.cl" \
  --set-env-vars="ALLOWED_ORIGINS=https://tallerinspeccion.tapsolutions.cl,https://admin.tallerinspeccion.tapsolutions.cl,https://cliente.tallerinspeccion.tapsolutions.cl" \
  --set-env-vars="LOG_LEVEL=INFO" \
  --set-env-vars="DEBUG=false" \
  --set-secrets="JWT_SECRET_KEY=taller-jwt-secret-key:latest" \
  --set-secrets="HMAC_SECRET_KEY=taller-hmac-secret-key:latest" \
  --set-secrets="/secrets/firebase_credentials.json=taller-firebase-credentials:latest"

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe tallerapp-api \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(status.url)")
echo "Backend URL: $SERVICE_URL"

cd ..
```

### Fase C — Verificar backend

```bash
# Health check
curl -s "$SERVICE_URL/api/v1/health" | python3 -m json.tool

# Docs del API
echo "Documentación: $SERVICE_URL/api/v1/openapi.json"
```

Respuesta esperada:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "production"
}
```

### Fase D — Seed de datos iniciales

```bash
# Crear SuperAdmin, tenant platform y planes
# (El script usa las credenciales locales de Firebase)
make seed
```

### Fase E — Deploy de Firestore Rules e Índices

```bash
firebase deploy --only firestore --project="$PROJECT_ID"
firebase deploy --only storage --project="$PROJECT_ID"
```

### Fase F — Build y deploy de Flutter Web

```bash
# Crear apps/cliente/.dart-defines.json con valores de producción
cat > apps/cliente/.dart-defines.json << EOF
{
  "API_BASE_URL": "https://api.tallerinspeccion.tapsolutions.cl",
  "ENVIRONMENT": "production",
  "APP_VERSION": "1.0.0",
  "FIREBASE_API_KEY": "TU_API_KEY",
  "FIREBASE_AUTH_DOMAIN": "$PROJECT_ID.firebaseapp.com",
  "FIREBASE_PROJECT_ID": "$PROJECT_ID",
  "FIREBASE_STORAGE_BUCKET": "$PROJECT_ID.appspot.com",
  "FIREBASE_MESSAGING_SENDER_ID": "TU_SENDER_ID",
  "FIREBASE_APP_ID": "TU_APP_ID",
  "FIREBASE_MEASUREMENT_ID": "G-XXXXXXXXXX"
}
EOF

# Build y deploy del portal cliente
make build-cliente
firebase deploy --only hosting:web-cliente --project="$PROJECT_ID"

echo "Portal cliente: https://cliente.tallerinspeccion.tapsolutions.cl"
```

### Fase G — Configurar dominio personalizado

Ver `docs/DOMAIN_CONFIGURATION.md` para instrucciones completas de DNS.

```bash
# Dominio del API (Cloud Run)
gcloud run domain-mappings create \
  --service=tallerapp-api \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region="$REGION" \
  --project="$PROJECT_ID"

# GCP mostrará los registros DNS a configurar en tu proveedor
gcloud run domain-mappings describe \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region="$REGION" --project="$PROJECT_ID"
```

El SSL se provisiona automáticamente (puede tardar hasta 24h en verificarse).

### Fase H — Validación final

```bash
echo "=== Validación del deployment ==="

API="https://api.tallerinspeccion.tapsolutions.cl"
CLIENTE="https://cliente.tallerinspeccion.tapsolutions.cl"

# Backend
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health")
echo "Backend health ($API): $STATUS"

# Portal cliente
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLIENTE")
echo "Portal cliente ($CLIENTE): $STATUS"

# HTTPS forzado
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://api.tallerinspeccion.tapsolutions.cl/api/v1/health")
echo "HTTP redirect (debe ser 301): $HTTP_STATUS"
```

---

## Despliegues posteriores (automáticos)

Después del primer setup, los deploys son automáticos via GitHub Actions:

```
git commit -m "feat: nueva funcionalidad"
git push origin main
# → CI corre automáticamente (lint + test + flutter analyze)
# → Si CI pasa → Deploy a Cloud Run + Firebase Hosting
```

Ver estado en: `github.com/TU_ORG/tallerapp/actions`

### Deploy manual de emergencia

```bash
# Backend
gh workflow run deploy-backend.yml --ref main

# Hosting
gh workflow run deploy-hosting.yml --ref main --field target=all

# O directamente con gcloud (si CI/CD no está disponible)
cd backend
docker build -t "$IMAGE:hotfix" .
docker push "$IMAGE:hotfix"
gcloud run deploy tallerapp-api --image "$IMAGE:hotfix" \
  --region="$REGION" --project="$PROJECT_ID"
```

---

## Rollback

### Backend — Traffic splitting en Cloud Run

```bash
# Ver revisiones disponibles
gcloud run revisions list \
  --service=tallerapp-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="table(name,status.observedGeneration,metadata.creationTimestamp)"

# Rollback al 100% a la revisión anterior
PREV_REVISION="tallerapp-api-00002-xxx"  # Nombre de la revisión anterior
gcloud run services update-traffic tallerapp-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --to-revisions="$PREV_REVISION=100"
```

### Hosting — Rollback en Firebase Console

```
Firebase Console → Hosting → [seleccionar sitio]
→ Release history
→ Rollback a la versión anterior (botón en cada release)
```

---

## Checklist de primer despliegue

### GCP/Backend
- [ ] Secretos creados en Secret Manager (JWT, HMAC, Firebase credentials)
- [ ] SA `tallerapp-backend` con permisos correctos
- [ ] Artifact Registry creado: `us-central1-docker.pkg.dev/taller-85514/tallerapp`
- [ ] Cloud Run service `tallerapp-api` corriendo
- [ ] `GET /api/v1/health` devuelve HTTP 200
- [ ] Dominio `api.tallerinspeccion.tapsolutions.cl` apuntando a Cloud Run
- [ ] SSL activo en `api.tallerinspeccion.tapsolutions.cl`

### Firebase/Hosting
- [ ] Firestore rules desplegadas (no en modo test)
- [ ] Firestore índices desplegados
- [ ] Storage rules desplegadas
- [ ] Storage CORS configurado
- [ ] Portal cliente desplegado en `web-cliente` target
- [ ] Dominio `cliente.tallerinspeccion.tapsolutions.cl` conectado y verificado
- [ ] SSL activo en `cliente.tallerinspeccion.tapsolutions.cl`

### Datos iniciales
- [ ] `make seed` ejecutado — SuperAdmin creado en Firebase Auth + Firestore
- [ ] Login con SuperAdmin funciona en panel admin (cuando esté listo)
- [ ] Planes en Firestore: `plans/starter`, `plans/professional`, `plans/enterprise`

### CI/CD
- [ ] Workload Identity Federation configurado
- [ ] GitHub Variables y Secrets configurados
- [ ] Push de prueba a `main` → CI pasa → Deploy automático funciona

### Monitoreo
- [ ] Uptime check creado en Cloud Monitoring
- [ ] Alertas de email configuradas para errores 5xx
- [ ] Presupuesto de billing con alertas al 50%, 90%, 100%

---

## Ambiente de Staging (opcional)

Para tener un ambiente de pruebas antes de producción:

1. Crear proyecto Firebase separado: `taller-85514-staging`
2. Duplicar Secrets en Secret Manager del proyecto staging
3. Crear segundo Cloud Run service: `tallerapp-api-staging`
4. Configurar GitHub Environment `staging` con sus propias Variables/Secrets
5. Agregar workflow que deploy a staging en push a `develop`

```bash
# Deploy a staging (ejemplo manual)
gcloud run deploy tallerapp-api-staging \
  --image "$IMAGE:latest" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  # ... resto de flags igual que producción
```
