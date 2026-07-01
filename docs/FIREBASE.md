# Firebase — Configuración Completa

> Guía para configurar todos los servicios de Firebase del proyecto.
> Prerrequisito: proyecto GCP creado (`docs/GOOGLE_CLOUD.md`).

---

## Variables de referencia

```bash
export PROJECT_ID="taller-85514"
export FIREBASE_CLI="firebase --project=$PROJECT_ID"
```

---

## Authentication

### Configurar en Firebase Console

```
Firebase Console → Authentication → Sign-in method
```

| Proveedor | Estado | Configuración |
|---|---|---|
| Email/Contraseña | ✅ Habilitar | Sin link de email |
| Anónimo | ❌ Deshabilitar | No se usa |
| Google | ⏳ Fase 14+ | Para login social (futuro) |
| Teléfono | ⏳ Fase 14+ | Para 2FA (futuro) |

### Configuración de seguridad

```
Firebase Console → Authentication → Settings
```

- **Email enumeration protection:** ✅ Activar (previene que atacantes descubran emails registrados)
- **Password policy:** Mínimo 8 caracteres, requerir letras y números
- **User account blocking:** Bloquear después de 10 intentos fallidos
- **Multi-factor authentication:** Preparado para activar en Fase 14+

### Templates de email

```
Firebase Console → Authentication → Templates
```

Personalizar con branding de Taller Inspección:
- **Email verification** — Cambiar remitente a `noreply@tallerinspeccion.tapsolutions.cl`
- **Password reset** — Cambiar URL a `https://admin.tallerinspeccion.tapsolutions.cl/reset-password`
- **Email change notification**

Para usar dominio personalizado en emails de Auth:
```
Authentication → Templates → Email address verification
→ Customize action URL
→ https://admin.tallerinspeccion.tapsolutions.cl/__/auth/action
```

### Authorized domains

```
Authentication → Settings → Authorized domains
```

Agregar:
- `tallerinspeccion.tapsolutions.cl`
- `admin.tallerinspeccion.tapsolutions.cl`
- `cliente.tallerinspeccion.tapsolutions.cl`
- `localhost` (ya está por defecto)

---

## Firestore

### Crear base de datos

```bash
# Modo producción (las rules definen el acceso — NO modo test)
gcloud firestore databases create \
  --project="$PROJECT_ID" \
  --location=nam5 \
  --type=firestore-native
```

> **Ubicación `nam5` (US Central):** Seleccionada para coherencia con Cloud Run en `us-central1`. Para menor latencia desde Chile, considerar `southamerica-east1` (São Paulo).

### Deploy de Rules e Índices

```bash
cd /ruta/al/proyecto

# Deploy de rules
firebase deploy --only firestore:rules --project="$PROJECT_ID"

# Deploy de índices (puede tardar varios minutos)
firebase deploy --only firestore:indexes --project="$PROJECT_ID"

# Ambos juntos
firebase deploy --only firestore --project="$PROJECT_ID"
```

### Verificar rules activas

```bash
# Ver rules actuales
firebase firestore:rules:get --project="$PROJECT_ID"
```

### Estructura de colecciones

Ver `docs/FIRESTORE.md` para el esquema completo. Colecciones principales:

```
tenants/                    # Un doc por taller
users/                      # Usuarios del sistema
clients/                    # Clientes de los talleres
vehicles/                   # Vehículos
inspections/                # Inspecciones precompra
  /{id}/items/              # Ítems de la inspección
inspection_templates/       # Plantillas configurables
estimates/                  # Presupuestos
  /{id}/items/
work_orders/                # Órdenes de trabajo
  /{id}/entries/            # Bitácora
public_tokens/              # Tokens HMAC para QR y presupuestos
audit_logs/                 # Audit trail inmutable
plans/                      # Planes SaaS
refresh_tokens/             # Refresh tokens (TTL 30 días)
```

### Configurar TTL para tokens expirados (opcional)

Firestore soporta TTL automático. Para activar en `refresh_tokens`:

```
Firebase Console → Firestore → Indexes → Pestaña "Exemptions"
→ No aplica para TTL

Firebase Console → Firestore → Data → Colección refresh_tokens
→ Configurar campo "expiresAt" como TTL policy
```

> Alternativamente, usar Cloud Scheduler + Cloud Run para limpiar tokens expirados (ver Fase 19).

---

## Storage

### Crear bucket (se crea automáticamente con Firebase)

El bucket `taller-85514.appspot.com` se crea al inicializar Firebase Storage.

### Deploy de Storage Rules

```bash
firebase deploy --only storage --project="$PROJECT_ID"
```

### Estructura de carpetas en Storage

```
tenants/{tenantId}/
  reports/              # PDFs generados de inspecciones
  logos/                # Logos de los talleres
  branding/             # Assets de branding (colores, fuentes)

public/
  qr/                   # Imágenes QR (no sensibles)
```

### Configurar CORS para Storage (Flutter Web y portal cliente)

Crear `infra/firebase/storage-cors.json`:

```json
[
  {
    "origin": [
      "https://tallerinspeccion.tapsolutions.cl",
      "https://admin.tallerinspeccion.tapsolutions.cl",
      "https://cliente.tallerinspeccion.tapsolutions.cl",
      "http://localhost:*"
    ],
    "method": ["GET", "HEAD"],
    "maxAgeSeconds": 3600,
    "responseHeader": ["Content-Type", "Content-Disposition"]
  }
]
```

Aplicar:
```bash
gsutil cors set infra/firebase/storage-cors.json gs://taller-85514.appspot.com
```

---

## Hosting

### Inicializar y configurar sitios múltiples

```bash
# Crear segundo sitio para portal de clientes
# (el sitio principal taller-85514 se crea automáticamente)
firebase hosting:sites:create taller-cliente-85514 \
  --project="$PROJECT_ID"

# Verificar sitios disponibles
firebase hosting:sites:list --project="$PROJECT_ID"
```

### Configurar targets en `.firebaserc`

Ya configurado en el proyecto:
```json
"targets": {
  "taller-85514": {
    "hosting": {
      "web-admin":   ["taller-85514"],
      "web-cliente": ["taller-cliente-85514"]
    }
  }
}
```

### Deploy inicial

```bash
# Deploy ambos targets
firebase deploy --only hosting --project="$PROJECT_ID"

# Deploy solo cliente
firebase deploy --only hosting:web-cliente --project="$PROJECT_ID"

# Deploy solo admin
firebase deploy --only hosting:web-admin --project="$PROJECT_ID"
```

### Conectar dominios personalizados

En Firebase Console → Hosting → seleccionar cada sitio:

**Sitio web-admin** (`taller-85514`):
1. "Add custom domain"
2. Dominio: `admin.tallerinspeccion.tapsolutions.cl`
3. Firebase dará registros DNS (A records) para agregar en tu proveedor
4. Verificación automática (puede tardar 24-48h)
5. SSL se provisiona automáticamente

**Sitio web-cliente** (`taller-cliente-85514`):
1. "Add custom domain"
2. Dominio: `cliente.tallerinspeccion.tapsolutions.cl`
3. Mismo proceso

Ver `docs/DOMAIN_CONFIGURATION.md` para instrucciones DNS detalladas.

---

## Cloud Messaging (FCM)

### Configuración web (Flutter Web)

```
Firebase Console → Proyecto → Configuración → Cloud Messaging
→ Web Push certificates → Generate key pair
```

Copiar la VAPID key a `apps/cliente/.dart-defines.json` y `apps/web_admin/.dart-defines.json`.

### Configuración Android

1. Descargar `google-services.json` desde Firebase Console → Configuración → Tus apps → Android
2. Guardar en `apps/mobile/android/app/google-services.json`
3. No commitear si el repo es público y contiene datos sensibles

### Configuración iOS

1. Descargar `GoogleService-Info.plist`
2. Guardar en `apps/mobile/ios/Runner/GoogleService-Info.plist`
3. Registrar APNs en Firebase: Configuración → Cloud Messaging → APNs certificates

---

## Analytics

### Activar Google Analytics

Al crear el proyecto Firebase, activar Google Analytics y vincularlo a una propiedad GA4.

```
Firebase Console → Analytics → Dashboard
```

Analytics está disponible automáticamente en:
- Apps Flutter con `firebase_analytics` package
- Firebase Hosting (mide page views)

### Eventos personalizados a registrar (Fase 15+)

| Evento | Descripción | Parámetros |
|---|---|---|
| `inspection_created` | Nueva inspección iniciada | `tenant_id`, `template_id` |
| `inspection_completed` | Inspección completada | `tenant_id`, `score` |
| `estimate_sent` | Presupuesto enviado al cliente | `tenant_id`, `amount` |
| `estimate_accepted` | Presupuesto aceptado | `tenant_id`, `amount` |
| `pdf_generated` | PDF generado | `tenant_id`, `type` |
| `qr_scanned` | QR escaneado por cliente | `tenant_id` |

---

## Crashlytics

### Setup en Flutter

Agregar al `pubspec.yaml` de cada app:
```yaml
dependencies:
  firebase_crashlytics: ^3.0.0
```

En `main.dart`:
```dart
await Firebase.initializeApp();
FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
```

```
Firebase Console → Crashlytics
→ Seguir las instrucciones para cada plataforma
```

---

## Performance Monitoring

Mide tiempos de carga y latencia de red en las apps Flutter.

```yaml
# pubspec.yaml (cada app Flutter)
dependencies:
  firebase_performance: ^0.9.0
```

```
Firebase Console → Performance
→ Monitorea automáticamente page load times y HTTP requests
```

---

## Remote Config (preparado)

Remote Config permite cambiar comportamiento de las apps sin publicar una nueva versión.
Útil para: feature flags, mensajes de mantenimiento, configuración de UI.

**Estado:** Preparado pero no implementado aún.

```
Firebase Console → Remote Config → Create configuration
```

Keys planificadas para el futuro:

| Key | Default | Descripción |
|---|---|---|
| `ai_features_enabled` | `false` | Habilita análisis IA (Fase IA) |
| `maintenance_mode` | `false` | Muestra banner de mantenimiento |
| `max_items_per_inspection` | `150` | Límite de ítems configurable |
| `pdf_watermark_enabled` | `false` | Marca de agua en PDFs del plan Starter |

---

## App Check (preparado)

App Check verifica que las requests al backend vienen de apps legítimas, no bots.

**Estado:** Preparado para activar. Requiere configuración por plataforma.

### Cuándo activar

Activar App Check en producción cuando:
- La app esté publicada en Play Store y App Store
- Se hayan verificado todos los proveedores (reCAPTCHA Enterprise para web)
- Se haya probado en staging que no rompe el flujo

### Proveedores por plataforma

| Plataforma | Proveedor |
|---|---|
| Android | Play Integrity API |
| iOS | App Attest (iOS 14+) / DeviceCheck (legacy) |
| Flutter Web | reCAPTCHA Enterprise |

### Habilitar

```
Firebase Console → App Check → Apps → [seleccionar app]
→ Registrar proveedor por plataforma
→ Enforced (modo estricto) — solo después de verificar en staging
```

> ⚠️ **No activar "Enforced"** hasta haber probado completamente en staging. En modo Enforced, cualquier request sin un App Check token válido es rechazada.

---

## Emulador Suite (desarrollo local)

```bash
# Iniciar todos los emuladores definidos en firebase.json
firebase emulators:start --project="$PROJECT_ID"

# Solo Firestore y Auth
firebase emulators:start --only firestore,auth

# Con datos importados de una sesión anterior
firebase emulators:start --import=./emulator-data

# UI: http://localhost:4000
```

---

## Mantenimiento y operaciones

### Exportar datos de Firestore (backup manual)

```bash
DATE=$(date +%Y%m%d)
gcloud firestore export gs://taller-85514.appspot.com/backups/firestore-$DATE \
  --project="$PROJECT_ID"
```

Ver `docs/BACKUPS.md` para la estrategia completa de respaldo.

### Verificar uso y cuotas

```
Firebase Console → Proyecto → Uso y facturación
```

Plan Spark (gratuito) límites relevantes:
- Firestore reads: 50K/día
- Firestore writes: 20K/día
- Storage: 1GB
- Hosting: 10GB/mes

Plan Blaze (pago por uso) recomendado para producción.

---

## Checklist Firebase

- [ ] Authentication habilitado con Email/Contraseña
- [ ] Authentication — Dominios autorizados configurados
- [ ] Firestore en modo producción (no modo test)
- [ ] Firestore rules y indexes desplegados
- [ ] Storage rules desplegadas
- [ ] Storage CORS configurado
- [ ] Hosting — dos sitios creados (web-admin + web-cliente)
- [ ] Hosting — dominios personalizados conectados y verificados
- [ ] FCM — Web Push certificate generado
- [ ] Analytics habilitado
- [ ] Crashlytics configurado en apps Flutter
- [ ] Performance Monitoring configurado
- [ ] App Check preparado (no enforced aún)
