# Variables de Entorno — Referencia Completa

> Fuente oficial de documentación de variables de entorno.
> Cada sección corresponde a un componente del sistema.

---

## Cómo funcionan las variables por componente

| Componente | Mecanismo | Archivo |
|---|---|---|
| Backend FastAPI | `.env` (pydantic-settings) | `backend/.env` |
| Flutter Web (cliente) | `--dart-define` en compilación | `apps/cliente/.dart-defines.json` |
| Flutter Web (admin) | `--dart-define` en compilación | `apps/web_admin/.dart-defines.json` |
| Flutter Mobile | `--dart-define` en compilación | `apps/mobile/.dart-defines.json` |
| CI/CD (GitHub Actions) | GitHub Secrets | `.github/workflows/*.yml` |
| Cloud Run (producción) | Google Secret Manager | Ver `docs/GOOGLE_CLOUD.md` |

> **Regla de oro:** Nunca hardcodear secretos. Nunca commitear `.env` ni `*.dart-defines.json`. Siempre usar los `.example` como plantilla.

---

## Backend FastAPI — `backend/.env`

### Aplicación

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `ENVIRONMENT` | string | `development` | ✓ | `development` \| `staging` \| `production` |
| `DEBUG` | bool | `false` | ✓ | `true` solo en desarrollo. Nunca en producción. |
| `PROJECT_NAME` | string | `Taller Inspección API` | — | Nombre en OpenAPI docs |
| `VERSION` | string | `0.1.0` | — | Versión del API |
| `LOG_LEVEL` | string | `INFO` | — | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |

### URLs

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `PUBLIC_BASE_URL` | string | `https://tallerinspeccion.tapsolutions.cl` | ✓ | URL base en tokens QR y presupuestos públicos |

### CORS

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `ALLOWED_ORIGINS` | list | `http://localhost:*` | ✓ | Orígenes permitidos, separados por coma. En producción: solo HTTPS con dominios reales. |

**Producción:**
```
ALLOWED_ORIGINS=https://tallerinspeccion.tapsolutions.cl,https://admin.tallerinspeccion.tapsolutions.cl,https://cliente.tallerinspeccion.tapsolutions.cl
```

### Google Cloud Platform

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `GCP_PROJECT_ID` | string | `taller-85514` | ✓ | ID del proyecto GCP |
| `USE_SECRET_MANAGER` | bool | `false` | ✓ | `true` en Cloud Run: lee secretos desde Secret Manager en lugar de `.env` |

### Firebase Admin SDK

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `FIREBASE_PROJECT_ID` | string | `taller-85514` | ✓ | ID del proyecto Firebase |
| `FIREBASE_CREDENTIALS_PATH` | string | `firebase_credentials.json` | ✓ | Ruta al Service Account JSON. Ignorado si `USE_SECRET_MANAGER=true`. |
| `FIREBASE_STORAGE_BUCKET` | string | `taller-85514.appspot.com` | ✓ | Bucket para PDFs, imágenes y logos |

**Generar credenciales:**
```
Firebase Console → Configuración del proyecto → Cuentas de servicio
→ "Generar nueva clave privada" → Guardar como firebase_credentials.json
```

### JWT Interno

> Complementa Firebase Auth. No lo reemplaza. Los JWTs internos llevan `tenant_id`, `role` y `permissions[]`.

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `JWT_SECRET_KEY` | string | — | ✓✓ | Clave HMAC para firmar JWTs internos. Generar: `openssl rand -hex 32` |
| `JWT_ALGORITHM` | string | `HS256` | — | Algoritmo de firma |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `30` | — | Expiración del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `30` | — | Expiración del refresh token |

### Tokens Públicos (HMAC)

> Para URLs públicas de informes QR y presupuestos. Firmados con HMAC-SHA256.

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `HMAC_SECRET_KEY` | string | — | ✓✓ | Clave para tokens públicos. **Diferente** a `JWT_SECRET_KEY`. Generar: `openssl rand -hex 32` |
| `QR_TOKEN_EXPIRY_DAYS` | int | `365` | — | Validez de tokens QR de inspección |

### Rate Limiting

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `RATE_LIMIT_CALLS` | int | `60` | — | Máximo de llamadas por ventana |
| `RATE_LIMIT_PERIOD_SECONDS` | int | `60` | — | Duración de la ventana en segundos |
| `RATE_LIMIT_AUTH_CALLS` | int | `10` | — | Límite más estricto para `/auth/*` |

### Email — SendGrid

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `SENDGRID_API_KEY` | string | — | (Fase 15) | API key de SendGrid. Obtener en: https://app.sendgrid.com/settings/api_keys |
| `SENDGRID_FROM_EMAIL` | string | `noreply@tallerinspeccion.tapsolutions.cl` | — | Email remitente |
| `SENDGRID_FROM_NAME` | string | `Taller Inspección` | — | Nombre del remitente |

### Email — SMTP (alternativa)

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `SMTP_HOST` | string | — | (Fase 15) | Host SMTP. Ej: `smtp.gmail.com` |
| `SMTP_PORT` | int | `587` | — | Puerto SMTP |
| `SMTP_USER` | string | — | — | Usuario SMTP |
| `SMTP_PASSWORD` | string | — | — | Contraseña SMTP |
| `SMTP_TLS` | bool | `true` | — | Usar STARTTLS |

### WhatsApp — Twilio

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `TWILIO_ACCOUNT_SID` | string | — | (Fase 15) | Account SID de Twilio |
| `TWILIO_AUTH_TOKEN` | string | — | — | Auth token de Twilio |
| `TWILIO_WHATSAPP_FROM` | string | — | — | Número WhatsApp. Formato: `whatsapp:+14155238886` |

### PDF

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `PDF_MAX_WORKERS` | int | `2` | — | Workers paralelos para generación de PDF |
| `PDF_TIMEOUT_SECONDS` | int | `30` | — | Timeout por PDF |

### Monitoring

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `SENTRY_DSN` | string | — | (producción) | DSN de Sentry para error tracking. Obtener en: https://sentry.io |

### Workers Internos

| Variable | Tipo | Default | Requerido | Descripción |
|---|---|---|---|---|
| `WORKERS_URL` | string | — | (Fase 19) | URL del servicio de workers en Cloud Run |
| `WORKERS_API_KEY` | string | — | (Fase 19) | API key para autenticación interna |

---

## Flutter — Mecanismo de dart-defines

Las apps Flutter usan `--dart-define` o `--dart-define-from-file` en lugar de `.env`.

### Leer una variable en Dart

```dart
// lib/core/config/app_config.dart
static const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);
```

### Archivo de dart-defines para desarrollo

Crear `apps/cliente/.dart-defines.json` (está en `.gitignore`):

```json
{
  "API_BASE_URL": "http://localhost:8000",
  "ENVIRONMENT": "development",
  "APP_VERSION": "1.0.0",
  "FIREBASE_API_KEY": "...",
  "FIREBASE_AUTH_DOMAIN": "taller-85514.firebaseapp.com",
  "FIREBASE_PROJECT_ID": "taller-85514",
  "FIREBASE_STORAGE_BUCKET": "taller-85514.appspot.com",
  "FIREBASE_MESSAGING_SENDER_ID": "...",
  "FIREBASE_APP_ID": "...",
  "FIREBASE_MEASUREMENT_ID": "..."
}
```

Usar en CLI:
```bash
flutter run -d chrome --dart-define-from-file=.dart-defines.json
flutter build web --dart-define-from-file=.dart-defines.json
```

---

## Portal del Cliente — `apps/cliente`

| Variable dart-define | Default | Descripción |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | URL del backend FastAPI |
| `ENVIRONMENT` | `development` | Ambiente activo |
| `APP_VERSION` | `1.0.0` | Versión de la app |
| `FIREBASE_API_KEY` | — | Clave pública Firebase Web |
| `FIREBASE_AUTH_DOMAIN` | `taller-85514.firebaseapp.com` | Dominio auth Firebase |
| `FIREBASE_PROJECT_ID` | `taller-85514` | ID proyecto Firebase |
| `FIREBASE_STORAGE_BUCKET` | `taller-85514.appspot.com` | Bucket Firebase Storage |
| `FIREBASE_MESSAGING_SENDER_ID` | — | Sender ID para FCM web |
| `FIREBASE_APP_ID` | — | App ID Firebase Web |
| `FIREBASE_MEASUREMENT_ID` | — | Measurement ID para Analytics |

> **Nota:** Las variables `FIREBASE_*` del portal de cliente son **públicas** por diseño — van en el bundle JavaScript y son visibles. La seguridad se garantiza con Firestore Security Rules y App Check, no ocultando estos valores.

---

## Panel Administrativo — `apps/web_admin`

Mismas variables que Portal del Cliente. Ver `apps/web_admin/.env.example`.

---

## App Mobile — `apps/mobile`

| Variable dart-define | Default | Descripción |
|---|---|---|
| `API_BASE_URL` | `http://10.0.2.2:8000` | URL backend. `10.0.2.2` es `localhost` del host en Android emulator. |
| `ENVIRONMENT` | `development` | Ambiente activo |
| `APP_VERSION` | `1.0.0` | Versión de la app |
| `FIREBASE_PROJECT_ID` | `taller-85514` | ID proyecto Firebase |
| `DB_NAME` | `taller_local.db` | Nombre de la base SQLite local (Drift) |
| `SYNC_INTERVAL_SECONDS` | `30` | Intervalo de sincronización offline |
| `MAX_SYNC_RETRY` | `3` | Reintentos máximos de sync |

**Configuración Firebase Mobile:**
- Android: `google-services.json` en `apps/mobile/android/app/`
- iOS: `GoogleService-Info.plist` en `apps/mobile/ios/Runner/`
- Descargar desde: Firebase Console → Configuración del proyecto → Tus apps

---

## CI/CD — GitHub Secrets

Configurar en: `GitHub → Repository → Settings → Secrets and variables → Actions`

| Secret | Usado en | Descripción |
|---|---|---|
| `GCP_SERVICE_ACCOUNT_KEY` | Deploy backend | JSON de Service Account con permisos Cloud Run + Storage |
| `FIREBASE_TOKEN` | Deploy hosting | Token de Firebase CLI (`firebase login:ci`) |
| `JWT_SECRET_KEY` | Backend config | Igual que backend `.env` |
| `HMAC_SECRET_KEY` | Backend config | Igual que backend `.env` |
| `FIREBASE_CREDENTIALS_JSON` | Backend config | Contenido del `firebase_credentials.json` |
| `SENDGRID_API_KEY` | Notificaciones | API key SendGrid |
| `SENTRY_DSN` | Monitoring | DSN de Sentry |
| `FLUTTER_FIREBASE_API_KEY_WEB` | Build Flutter Web | Firebase API Key para web |
| `FLUTTER_FIREBASE_APP_ID_ADMIN` | Build web_admin | App ID Firebase para panel admin |
| `FLUTTER_FIREBASE_APP_ID_CLIENTE` | Build cliente | App ID Firebase para portal cliente |

---

## Google Cloud Secret Manager (Producción)

Cuando `USE_SECRET_MANAGER=true`, el backend lee estas variables desde Secret Manager en lugar del `.env`.

| Secret ID en GCP | Corresponde a |
|---|---|
| `taller-jwt-secret-key` | `JWT_SECRET_KEY` |
| `taller-hmac-secret-key` | `HMAC_SECRET_KEY` |
| `taller-firebase-credentials` | Contenido del JSON de Service Account |
| `taller-sendgrid-api-key` | `SENDGRID_API_KEY` |
| `taller-twilio-auth-token` | `TWILIO_AUTH_TOKEN` |
| `taller-sentry-dsn` | `SENTRY_DSN` |

Ver `docs/GOOGLE_CLOUD.md` para instrucciones de configuración.

---

## Variables que NO deben rotarse sin coordinación

| Variable | Impacto de rotación |
|---|---|
| `JWT_SECRET_KEY` | Invalida **todos** los access tokens y refresh tokens activos → logout masivo |
| `HMAC_SECRET_KEY` | Invalida **todos** los tokens QR e informes públicos existentes |
| `FIREBASE_CREDENTIALS_PATH` | Si el archivo cambia, el backend pierde acceso a Firestore y Auth |

**Procedimiento de rotación:**
1. Generar nuevo valor
2. Actualizar en Secret Manager / GitHub Secrets
3. Hacer rolling restart del backend
4. Los tokens emitidos con la clave anterior quedarán inválidos

---

## Checklist de verificación antes de desplegar

- [ ] `JWT_SECRET_KEY` generado con `openssl rand -hex 32` (no el de ejemplo)
- [ ] `HMAC_SECRET_KEY` generado con `openssl rand -hex 32` (diferente al anterior)
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `ALLOWED_ORIGINS` contiene solo dominios HTTPS reales
- [ ] `FIREBASE_CREDENTIALS_PATH` o `USE_SECRET_MANAGER=true` configurado
- [ ] Ningún `.env` ni `firebase_credentials.json` en el repositorio
- [ ] Variables de Flutter compiladas con `--dart-define` apuntando a API de producción
