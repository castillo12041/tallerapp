# Configuración de Dominios

> Configura el dominio principal, subdominios, DNS, HTTPS y subdominios por tenant.
> Dominio base: `tallerinspeccion.tapsolutions.cl` (subdominio de `tapsolutions.cl`).

---

## Arquitectura de dominios

```
tapsolutions.cl (dominio raíz — no administrado aquí)
└── tallerinspeccion.tapsolutions.cl
    ├── tallerinspeccion.tapsolutions.cl      → Firebase Hosting (landing / web-admin)
    ├── admin.tallerinspeccion.tapsolutions.cl → Firebase Hosting (panel administración)
    ├── cliente.tallerinspeccion.tapsolutions.cl → Firebase Hosting (portal cliente)
    ├── api.tallerinspeccion.tapsolutions.cl   → Cloud Run (backend FastAPI)
    └── *.tallerinspeccion.tapsolutions.cl     → Subdominios por tenant (Premium, Fase 14+)
        └── miTaller.tallerinspeccion.tapsolutions.cl → por tenant
```

---

## Registro DNS requerido

Agregar estos registros en el panel DNS de quien administra `tapsolutions.cl`.

### Paso 1 — Identificar los registros de Firebase Hosting

Firebase genera los registros DNS al conectar el dominio personalizado:

```
Firebase Console → Hosting → [sitio web-admin] → Add custom domain
→ Ingresar: tallerinspeccion.tapsolutions.cl
→ Firebase mostrará los registros A y TXT necesarios
```

Hacer lo mismo para cada subdominio.

### Paso 2 — Identificar el registro del API (Cloud Run)

```bash
# Crear domain mapping y ver los registros necesarios
gcloud run domain-mappings create \
  --service=tallerapp-api \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region=us-central1 \
  --project=taller-85514

# Ver instrucciones DNS
gcloud run domain-mappings describe \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region=us-central1 \
  --project=taller-85514 \
  --format="yaml(status.resourceRecords)"
```

### Paso 3 — Agregar registros en el panel DNS

Los valores exactos los provee Firebase/GCP en los pasos anteriores.
La estructura general es:

| Tipo | Host | Valor | TTL | Propósito |
|---|---|---|---|---|
| `TXT` | `tallerinspeccion.tapsolutions.cl` | `"firebase=..."` | 3600 | Verificación Firebase |
| `A` | `tallerinspeccion.tapsolutions.cl` | IP de Firebase | 3600 | Web admin (raíz) |
| `A` | `admin.tallerinspeccion.tapsolutions.cl` | IP de Firebase | 3600 | Panel admin |
| `A` | `cliente.tallerinspeccion.tapsolutions.cl` | IP de Firebase | 3600 | Portal cliente |
| `CNAME` | `api.tallerinspeccion.tapsolutions.cl` | `ghs.googlehosted.com` | 3600 | Backend API |
| `A` | `*.tallerinspeccion.tapsolutions.cl` | IP de Firebase | 3600 | Subdominios tenant (Premium) |

> **Nota sobre `tapsolutions.cl`:** Coordinar la adición de estos registros con quien administra el DNS del dominio raíz. Si tienes acceso directo al panel DNS de `tapsolutions.cl` (Cloudflare, Namecheap, GoDaddy, etc.), agregar los registros ahí.

---

## HTTPS y certificados SSL

### Firebase Hosting — SSL automático

Firebase Hosting provisiona certificados SSL automáticamente usando Let's Encrypt una vez que:
1. El dominio está verificado (TXT record)
2. Los registros A/CNAME apuntan a Firebase

**Tiempo de aprovisionamiento:** 24-48 horas después de agregar los registros DNS.

Verificar estado:
```
Firebase Console → Hosting → [sitio] → Custom domains
→ Estado: "Connected" con ícono verde ✓
```

### Cloud Run — SSL automático

Cloud Run también provisiona SSL automáticamente para domain mappings.

Verificar:
```bash
gcloud run domain-mappings describe \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region=us-central1 \
  --project=taller-85514 \
  --format="value(status.conditions)"
```

Buscar condición `CertificateProvisioned: True`.

### HTTPS forzado

**Firebase Hosting:** HTTPS forzado automáticamente. Cualquier request HTTP es redirigida a HTTPS con código 301. No requiere configuración.

**Cloud Run:** Requiere configurar en `firebase.json` si se usa el backend vía Hosting rewrites. En el caso de domain mapping directo a Cloud Run, el servicio acepta solo HTTPS por defecto.

Para el backend, agregar el header HSTS ya está en `firebase.json` para las apps web:
```json
{
  "key": "Strict-Transport-Security",
  "value": "max-age=31536000; includeSubDomains; preload"
}
```

---

## Rewrites en Firebase Hosting

El `firebase.json` ya tiene configurados los rewrites básicos (SPA routing):
```json
{ "source": "/**", "destination": "/index.html" }
```

### Rewrite del API vía Hosting (alternativa a domain mapping)

Si prefieres que `tallerinspeccion.tapsolutions.cl/api` apunte al backend en lugar de usar un subdominio separado para el API:

```json
{
  "hosting": [
    {
      "target": "web-admin",
      "rewrites": [
        {
          "source": "/api/**",
          "run": {
            "serviceId": "tallerapp-api",
            "region": "us-central1"
          }
        },
        {
          "source": "/**",
          "destination": "/index.html"
        }
      ]
    }
  ]
}
```

> **Decisión arquitectónica:** Recomendamos el subdominio separado `api.tallerinspeccion.tapsolutions.cl` (domain mapping directo a Cloud Run) en lugar del rewrite vía Hosting. Razones: menor latencia (evita un hop), CORS más simple, mayor claridad.

---

## Subdominios por Tenant (Feature Premium — Fase 14+)

Permite que cada taller tenga su propio subdominio:
```
miTaller.tallerinspeccion.tapsolutions.cl → Panel del taller
```

### Requerimientos técnicos

1. **Wildcard DNS:** Registro `*.tallerinspeccion.tapsolutions.cl` apuntando a Firebase Hosting
2. **Wildcard SSL:** Firebase Hosting soporta wildcard certificates
3. **Routing por subdominio:** La app Flutter Web lee el subdominio y carga el tenant correspondiente
4. **Firestore:** El `tenantId` se resuelve desde el subdominio

### Configuración wildcard en Firebase Hosting

```
Firebase Console → Hosting → [sitio web-admin] → Add custom domain
→ Ingresar: *.tallerinspeccion.tapsolutions.cl
→ Firebase emite certificado wildcard automáticamente
```

### Resolución del tenant en Flutter Web

```dart
// apps/web_admin/lib/core/config/tenant_resolver.dart
String? resolveTenantFromSubdomain() {
  // Solo en web
  if (!kIsWeb) return null;

  final hostname = Uri.base.host;
  // hostname = "mitaller.tallerinspeccion.tapsolutions.cl"
  final parts = hostname.split('.');
  
  // Si tiene más de 3 partes, el primer segmento es el slug del tenant
  if (parts.length > 3) {
    return parts.first;
  }
  return null; // Dominio raíz = sin subdominio de tenant
}
```

### Implementación completa (Fase 14+)

Esta feature requiere:
1. Campo `subdomain` en `tenants/{id}` (único)
2. Endpoint `GET /api/v1/tenants/by-subdomain/{subdomain}`
3. Cloud Function o middleware que valide el subdominio
4. Validación de unicidad del subdominio al crear/actualizar tenant

---

## Dominio personalizado por tenant (Plan Enterprise — Fase futura)

Permite que un taller use su propio dominio:
```
inspecciones.mitaller.cl → Portal del taller
```

### Implementación técnica

Esto requiere:
1. El tenant proporciona su dominio
2. El taller configura un CNAME en su DNS: `inspecciones.mitaller.cl → tallerinspeccion.tapsolutions.cl`
3. Firebase Hosting soporta múltiples dominios por sitio
4. Provisionar SSL via Let's Encrypt API o Firebase

```bash
# Agregar dominio de un tenant específico
firebase hosting:channel:deploy custom-domain \
  --only hosting:web-admin \
  --project="$PROJECT_ID"

# O via API de Firebase Admin SDK (automatizado)
```

> Esta feature es compleja y se implementa como parte de las Fases 17-18 (billing y customización avanzada).

---

## Verificación de dominios

```bash
#!/usr/bin/env bash
# Verificar que todos los dominios responden correctamente

echo "=== Verificación de dominios ==="

check_domain() {
  local domain=$1
  local expected_status=${2:-200}
  local status=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain")
  
  if [[ "$status" == "$expected_status" ]]; then
    echo "  ✓ https://$domain → $status"
  else
    echo "  ✗ https://$domain → $status (esperado: $expected_status)"
  fi
}

check_domain "tallerinspeccion.tapsolutions.cl"
check_domain "admin.tallerinspeccion.tapsolutions.cl"
check_domain "cliente.tallerinspeccion.tapsolutions.cl"
check_domain "api.tallerinspeccion.tapsolutions.cl/api/v1/health"

echo ""
echo "=== Verificación HTTPS (redirección HTTP→HTTPS) ==="
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "http://api.tallerinspeccion.tapsolutions.cl/api/v1/health")
echo "  HTTP redirect final: $HTTP_STATUS (esperado: 200 después de redirect)"

echo ""
echo "=== Verificación SSL ==="
for domain in \
  "tallerinspeccion.tapsolutions.cl" \
  "admin.tallerinspeccion.tapsolutions.cl" \
  "cliente.tallerinspeccion.tapsolutions.cl" \
  "api.tallerinspeccion.tapsolutions.cl"; do
  EXPIRY=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null \
    | openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2)
  echo "  SSL $domain: expira $EXPIRY"
done
```

---

## Troubleshooting DNS

### El dominio no resuelve después de 48h

```bash
# Verificar que los registros DNS se propagaron
dig tallerinspeccion.tapsolutions.cl A
dig api.tallerinspeccion.tapsolutions.cl CNAME
nslookup cliente.tallerinspeccion.tapsolutions.cl

# Usar un checker de propagación DNS
# https://dnschecker.org → ingresar tu dominio
```

### `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`

El certificado SSL aún no se ha aprovisionado. Esperar hasta 48h después de que los registros DNS se propaguen.

### Firebase Hosting muestra "Domain not connected"

1. Verificar que el TXT record de verificación esté en el DNS
2. El TTL bajo acelera la verificación (usar TTL=300 durante la configuración inicial)
3. Si después de 24h no verifica, contactar Firebase Support

### Cloud Run domain mapping en estado `Pending`

```bash
# Ver estado detallado
gcloud run domain-mappings describe \
  --domain=api.tallerinspeccion.tapsolutions.cl \
  --region=us-central1 \
  --project=taller-85514

# El campo status.conditions mostrará qué falta
```

---

## Resumen de dominios configurados

| Dominio | Apunta a | Estado | SSL |
|---|---|---|---|
| `tallerinspeccion.tapsolutions.cl` | Firebase Hosting (web-admin) | Pendiente configuración | Auto |
| `admin.tallerinspeccion.tapsolutions.cl` | Firebase Hosting (web-admin) | Pendiente configuración | Auto |
| `cliente.tallerinspeccion.tapsolutions.cl` | Firebase Hosting (web-cliente) | Pendiente configuración | Auto |
| `api.tallerinspeccion.tapsolutions.cl` | Cloud Run (tallerapp-api) | Pendiente configuración | Auto |
| `*.tallerinspeccion.tapsolutions.cl` | Firebase Hosting (wildcard, Premium) | Fase 14+ | Auto (wildcard) |
