# Security Checklist — Producción

> Lista de verificación de seguridad para cada despliegue a producción.
> Basada en OWASP Top 10 (2021), adaptada al stack del proyecto.

---

## Cómo usar este documento

- Revisar antes de cada **primer deploy** y cuando cambie la arquitectura de seguridad.
- Para deploys rutinarios de features, basta con la sección marcada con ⭐.
- Una casilla sin marcar es un bloqueador de producción.

---

## ⭐ Transport Security

### HTTPS

- [ ] Todo el tráfico usa HTTPS. No hay endpoints HTTP sin redirección.
- [ ] Firebase Hosting fuerza HTTPS (automático — verificar en Console).
- [ ] Cloud Run acepta solo HTTPS en el dominio personalizado.
- [ ] `Strict-Transport-Security` header configurado en todos los dominios:
  ```
  max-age=31536000; includeSubDomains; preload
  ```
- [ ] Certificados SSL activos y con más de 30 días de vigencia:
  ```bash
  echo | openssl s_client -connect api.tallerinspeccion.tapsolutions.cl:443 \
    -servername api.tallerinspeccion.tapsolutions.cl 2>/dev/null \
    | openssl x509 -noout -dates
  ```

---

## ⭐ Autenticación

### Firebase Auth

- [ ] Solo Email/Contraseña habilitado (no Anonymous, no providers no configurados).
- [ ] Email enumeration protection activado en Firebase Console.
- [ ] Bloqueo automático después de 10 intentos fallidos configurado.
- [ ] Tokens de Firebase Auth tienen TTL de 1 hora (configuración por defecto — no modificar).
- [ ] Los custom claims del JWT de Firebase incluyen `tenant_id` y `role`.

### JWT Interno

- [ ] `JWT_SECRET_KEY` generado con `openssl rand -hex 32` (no el valor de ejemplo).
- [ ] `JWT_SECRET_KEY` ≠ `HMAC_SECRET_KEY` (claves diferentes).
- [ ] Access token expira en 30 minutos (`ACCESS_TOKEN_EXPIRE_MINUTES=30`).
- [ ] Refresh token expira en 30 días (`REFRESH_TOKEN_EXPIRE_DAYS=30`).
- [ ] Refresh token rotation implementada — cada uso genera un nuevo token.
- [ ] Refresh tokens se invalidan al hacer logout.
- [ ] `JWT_SECRET_KEY` almacenado en Secret Manager, no en variables de entorno del código.

### Tokens Públicos (HMAC)

- [ ] `HMAC_SECRET_KEY` generado con `openssl rand -hex 32`.
- [ ] Tokens QR tienen expiración (365 días por defecto, configurable).
- [ ] Tokens de presupuesto verifican `token_type == "budget_access"` antes de procesar.
- [ ] Tokens revocados son rechazados inmediatamente (campo `is_valid` en Firestore).

---

## ⭐ Autorización

### RBAC

- [ ] Todos los endpoints de la API requieren autenticación (excepto `/health`, `/public/*`, `/auth/*`).
- [ ] Cada endpoint verifica el permiso específico con `require_permission("resource:action")`.
- [ ] El middleware extrae `tenant_id` del JWT y lo adjunta al request — no se acepta del body.
- [ ] Las queries de Firestore siempre incluyen `.where("tenantId", "==", tenant_id)`.
- [ ] No existe ningún endpoint que retorne datos de múltiples tenants mezclados.

### Multi-tenancy

- [ ] `TenantMiddleware` activo en todas las rutas protegidas.
- [ ] Los IDs de documentos en Firestore no son predecibles — usar UUIDs.
- [ ] Las URLs públicas usan tokens HMAC firmados, no IDs directos.
- [ ] Un usuario no puede acceder a recursos de otro tenant aunque conozca el ID.

---

## ⭐ Seguridad del API

### Rate Limiting

- [ ] Rate limiting activo: 60 requests/min/IP general.
- [ ] Rate limiting estricto en `/auth/*`: 10 requests/min/IP.
- [ ] `RateLimitMiddleware` es el middleware más externo (antes de auth).
- [ ] Las IPs de confianza no están exentas del rate limit.

### CORS

- [ ] `ALLOWED_ORIGINS` contiene SOLO los dominios de producción (no `*`).
- [ ] No hay `allow_credentials=True` con `allow_origins=["*"]`.
- [ ] CORS configurado en el middleware FastAPI, no solo en Firebase Hosting.

```python
# Verificar en backend/app/main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Validación de entrada

- [ ] Todos los request bodies usan `pydantic.BaseModel` con tipos estrictos.
- [ ] No existe `orm_mode` sin validación adicional en campos opcionales.
- [ ] Las longitudes máximas de strings están definidas (`max_length` en Pydantic).
- [ ] Los IDs recibidos son validados como strings no vacíos antes de queries Firestore.
- [ ] Los archivos subidos (logos, imágenes) tienen validación de tipo MIME y tamaño.

### Security Headers

- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: SAMEORIGIN`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Content-Security-Policy` configurado en Firebase Hosting (`firebase.json`)
- [ ] `Permissions-Policy: camera=(), microphone=(), geolocation=()`

Verificar headers en producción:
```bash
curl -I https://cliente.tallerinspeccion.tapsolutions.cl | grep -i "x-content\|x-frame\|strict-transport\|content-security"
```

---

## Seguridad de datos

### Firestore Security Rules

- [ ] Las rules están desplegadas (no en modo "test" o "allow all").
- [ ] Ninguna colección tiene `.allow read, write: if true`.
- [ ] Los usuarios solo pueden leer sus propios documentos de `users/{uid}`.
- [ ] Toda operación valida `request.auth.token.tenant_id == resource.data.tenantId`.
- [ ] Los documentos de `audit_logs` son append-only (sin update ni delete).
- [ ] Las reglas han sido testeadas con Firebase Emulator.

```bash
# Verificar rules activas (no deben ser las de desarrollo)
firebase firestore:rules:get --project=taller-85514
```

### Storage Security Rules

- [ ] Las rules de Storage están desplegadas.
- [ ] Los archivos solo son accesibles por el tenant propietario.
- [ ] Los PDFs en `tenants/{tenantId}/reports/` solo son legibles por el tenant.
- [ ] Tamaño máximo de upload definido en rules (ej: 10MB para logos).
- [ ] CORS de Storage configurado con solo los dominios permitidos.

### Soft Delete

- [ ] Ningún endpoint de negocio usa `document.delete()` en registros críticos.
- [ ] Los endpoints DELETE de inspecciones, presupuestos y OTs usan soft delete.
- [ ] Los registros soft-deleted no aparecen en listados (filtro `is_deleted == false`).

---

## Gestión de secretos

- [ ] Ningún secreto en el código fuente o en archivos commiteados.
- [ ] `.env` está en `.gitignore` (verificar con `git status backend/.env`).
- [ ] `firebase_credentials.json` está en `.gitignore`.
- [ ] GitHub Secrets configurados con los valores correctos de producción.
- [ ] Secret Manager tiene al menos las versiones de JWT, HMAC y Firebase credentials.
- [ ] Los secretos rotados se invalidan correctamente (ver `docs/ENVIRONMENT_VARIABLES.md`).

```bash
# Verificar que no hay secretos commiteados
git log --all --full-history -- backend/.env
git log --all --full-history -- backend/firebase_credentials.json
# Si hay resultados, los secretos están en el historial — requiere git-filter-repo
```

---

## Protección XSS

### Flutter Web

- [ ] No se usa `html` o `Element.setInnerHtml` con contenido del usuario.
- [ ] Los datos del usuario mostrados en UI usan widgets de Flutter (no HTML nativo).
- [ ] La CSP en `firebase.json` no incluye `unsafe-inline` para scripts de usuario.

### Backend

- [ ] Los endpoints no devuelven HTML (solo JSON) — no hay riesgo de reflected XSS.
- [ ] Los campos de texto libre son almacenados y devueltos sin modificación (no renderizados por el backend).

---

## Protección CSRF (Flutter Web)

Flutter Web no usa cookies de sesión — usa `Authorization: Bearer` header.
Los ataques CSRF requieren cookies. Por tanto, el riesgo es bajo.

Sin embargo:

- [ ] Los endpoints de mutación (POST/PATCH/DELETE) requieren el header `Authorization`.
- [ ] El header `Content-Type: application/json` es verificado en requests con body.
- [ ] No existen endpoints que acepten formularios HTML (`application/x-www-form-urlencoded`) con acciones destructivas.

---

## Infraestructura

### IAM — Least Privilege

- [ ] Service Account `tallerapp-backend` tiene SOLO los roles necesarios (Datastore User, Storage Admin, Secret Accessor).
- [ ] Service Account `github-deploy` tiene SOLO los roles de deploy (Run Admin, AR Writer).
- [ ] No hay Service Account con roles de Owner o Editor.
- [ ] Las claves de Service Account no se usan (se usa Workload Identity Federation).

### Cloud Run

- [ ] El servicio corre con `tallerapp-backend` SA (no con el SA por defecto).
- [ ] `--allow-unauthenticated` es apropiado (el backend maneja su propia auth con JWT).
- [ ] `min-instances=0` — sin tráfico, no hay costo.
- [ ] Variables de entorno sensibles provienen de Secret Manager, no de env vars directas.

### App Check (preparado)

- [ ] App Check NO está en modo Enforced hasta que todas las plataformas estén configuradas.
- [ ] Activar App Check solo después de verificar en staging.

---

## Dependencias

- [ ] `pip list --outdated` ejecutado — no hay vulnerabilidades conocidas en deps directas.
- [ ] `flutter pub outdated` ejecutado en cada app Flutter.
- [ ] Dependencias de Python con versiones pinneadas en rango (`>=X,<Y`).
- [ ] Sin dependencias con licencia incompatible con uso comercial.

```bash
# Verificar vulnerabilidades en Python (requiere pip-audit)
pip install pip-audit
pip-audit -r backend/requirements.prod.txt
```

---

## Antes de cada deploy a producción ⭐

Lista mínima a verificar en cada deploy:

- [ ] `make test` — todos los tests pasan
- [ ] `make lint` — sin errores de ruff ni mypy
- [ ] No hay claves secretas en el diff del PR (`git diff main...HEAD | grep -i "secret\|password\|key"`)
- [ ] Los endpoints nuevos tienen su permiso RBAC definido
- [ ] Los campos nuevos de Firestore tienen su regla en `firestore.rules`
- [ ] Variables de entorno nuevas documentadas en `docs/ENVIRONMENT_VARIABLES.md`
- [ ] CI/CD pasa (lint + test + flutter analyze)

---

## Incidente de seguridad — respuesta inicial

Si se detecta un acceso no autorizado o exposición de datos:

```bash
# 1. Revocar acceso inmediatamente si es una credencial comprometida
gcloud secrets versions disable taller-jwt-secret-key --secret=VERSION

# 2. Rotar el secreto comprometido
NEW_KEY=$(openssl rand -hex 32)
echo -n "$NEW_KEY" | gcloud secrets versions add taller-jwt-secret-key \
  --project=taller-85514 --data-file=-

# 3. Forzar re-deploy con el nuevo secreto
gh workflow run deploy-backend.yml --ref main

# 4. Revisar audit logs para determinar el alcance
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=WARNING' \
  --project=taller-85514 --limit=500 --format=json > audit_incident.json

# 5. Si hay usuarios afectados:
# - Revocar todos sus refresh tokens (Firestore: refresh_tokens collection)
# - Notificarles según normativa aplicable
```
