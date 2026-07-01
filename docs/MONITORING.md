# Monitoreo y Observabilidad

> Estrategia completa de observabilidad: logs, métricas, alertas, trazas y Crashlytics.

---

## Capas de observabilidad

```
┌─────────────────────────────────────────────────────────────┐
│  Usuarios (Flutter Apps)                                    │
│  ├── Firebase Crashlytics  → crashes y errores no capturados│
│  ├── Firebase Performance  → latencia de red y renders      │
│  └── Firebase Analytics    → eventos de uso y funnel        │
├─────────────────────────────────────────────────────────────┤
│  Backend (FastAPI en Cloud Run)                             │
│  ├── Cloud Logging         → logs estructurados JSON        │
│  ├── Cloud Monitoring      → métricas de Cloud Run + custom │
│  ├── Cloud Trace           → trazas de requests             │
│  └── Sentry                → error tracking con stack trace │
├─────────────────────────────────────────────────────────────┤
│  Infraestructura (GCP)                                      │
│  ├── Uptime Checks         → disponibilidad del API         │
│  ├── Budget Alerts         → costos anómalos                │
│  └── Audit Logs            → acciones de administración     │
└─────────────────────────────────────────────────────────────┘
```

---

## Logging estructurado — Backend

El backend debe emitir logs en formato JSON para que Cloud Logging pueda indexarlos y filtrarlos eficientemente.

### Configurar logging estructurado en FastAPI

Agregar a `backend/app/core/logging.py` (Fase 17):

```python
import json
import logging
import sys
from datetime import UTC, datetime

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Formatea logs como JSON para Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Contexto de request (si está disponible)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_entry["tenant_id"] = record.tenant_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)
    root.handlers = [handler]

    # Silenciar loggers ruidosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

### Campos estándar de logs

Cada log debe incluir:

| Campo | Descripción |
|---|---|
| `severity` | DEBUG / INFO / WARNING / ERROR / CRITICAL |
| `message` | Mensaje legible por humanos |
| `request_id` | UUID del request (del middleware) |
| `tenant_id` | Tenant en contexto (si aplica) |
| `user_id` | UID del usuario (si autenticado) |
| `action` | Acción de negocio (ej: `inspection.completed`) |
| `entity_type` | Tipo de entidad afectada |
| `entity_id` | ID de la entidad |
| `duration_ms` | Duración de la operación |

### Ver logs en Cloud Logging

```bash
# Logs del backend en tiempo real
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="tallerapp-api"' \
  --project=taller-85514 \
  --limit=50 \
  --format=json

# Solo errores
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --project=taller-85514 \
  --limit=20
```

### Filtros útiles en Cloud Logging Console

```
# Errores del backend
resource.type="cloud_run_revision"
resource.labels.service_name="tallerapp-api"
severity>=ERROR

# Requests de un tenant específico
resource.type="cloud_run_revision"
jsonPayload.tenant_id="TENANT_ID"

# Requests lentos (>2s)
resource.type="cloud_run_revision"
jsonPayload.duration_ms>2000

# Logins fallidos
resource.type="cloud_run_revision"
jsonPayload.action="auth.login.failed"
```

---

## Cloud Monitoring — Métricas y Alertas

### Métricas de Cloud Run (automáticas)

Cloud Monitoring recopila automáticamente:

| Métrica | Descripción | Alerta sugerida |
|---|---|---|
| `run.googleapis.com/request_count` | Requests por segundo | — |
| `run.googleapis.com/request_latencies` | Latencia de requests | p95 > 2000ms |
| `run.googleapis.com/container/instance_count` | Instancias activas | > 8 (de 10 máx) |
| `run.googleapis.com/container/cpu/utilizations` | CPU | > 80% |
| `run.googleapis.com/container/memory/utilizations` | Memoria | > 85% |

### Configurar políticas de alerta

En Cloud Console → Monitoring → Alerting → Create Policy:

**Alerta 1: Errores HTTP 5xx**
```
Metric: logging/user/backend-5xx-errors (log-based metric)
Condition: count > 10 in 5 minutes
Severity: Critical
Notification: Email peladocastillo@gmail.com
```

**Alerta 2: Latencia alta**
```
Metric: run.googleapis.com/request_latencies
Filter: service_name = "tallerapp-api"
Condition: p95 > 2000ms in 10 minutes
Severity: Warning
```

**Alerta 3: Instancias al límite**
```
Metric: run.googleapis.com/container/instance_count
Condition: value >= 9 (de 10 máximo configurado)
Severity: Warning
→ Acción: aumentar max-instances
```

**Alerta 4: Uptime caído**
```
Uptime check: tallerapp-health (creado en GOOGLE_CLOUD.md)
Condition: Uptime < 100% en últimas 5 minutes
Severity: Critical
Notification: Email inmediato
```

### Crear dashboard personalizado

En Cloud Console → Monitoring → Dashboards → Create:

Widgets recomendados:
1. **Request rate** — requests/segundo por Cloud Run
2. **Error rate** — % de 5xx en tiempo real
3. **Latency p50/p95/p99** — gráfico de latencia
4. **Instance count** — escaldo automático
5. **Firestore reads/writes** — operaciones por segundo
6. **Active users** — desde Firebase Analytics

---

## Health Check Endpoint

El backend ya expone `GET /api/v1/health`. Documentar qué valida:

```python
# backend/app/api/v1/health.py — mejorar con checks reales (Fase 17)

@router.get("/health")
async def health_check() -> dict:
    checks = {}

    # Verificar Firestore
    try:
        db = get_firestore()
        db.collection("_health").limit(1).get()
        checks["firestore"] = "ok"
    except Exception as e:
        checks["firestore"] = f"error: {e}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }
```

Usar en:
- Uptime check de Cloud Monitoring (cada 60s)
- Docker health check (en Dockerfile)
- GitHub Actions post-deploy validation

---

## Sentry — Error Tracking

Sentry captura errores con stack trace completo, contexto y breadcrumbs.

### Configurar en FastAPI

```bash
pip install sentry-sdk[fastapi]
```

```python
# backend/app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


def configure_sentry() -> None:
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
        ],
        traces_sample_rate=0.1,   # 10% de requests para performance
        profiles_sample_rate=0.1,
        send_default_pii=False,   # No enviar PII por defecto
        before_send=_filter_sensitive_data,
    )


def _filter_sensitive_data(event: dict, hint: dict) -> dict | None:
    """Eliminar campos sensibles antes de enviar a Sentry."""
    if "request" in event:
        headers = event["request"].get("headers", {})
        if "Authorization" in headers:
            headers["Authorization"] = "[Filtered]"
    return event
```

### Configurar en Flutter (Crashlytics + Sentry)

Para errores no capturados por Crashlytics:

```dart
// apps/mobile/lib/main.dart
import 'package:sentry_flutter/sentry_flutter.dart';

await SentryFlutter.init(
  (options) {
    options.dsn = const String.fromEnvironment('SENTRY_DSN');
    options.environment = const String.fromEnvironment('ENVIRONMENT');
    options.tracesSampleRate = 0.1;
  },
  appRunner: () => runApp(const ProviderScope(child: App())),
);
```

---

## Firebase Crashlytics

### Setup en Flutter

```yaml
# pubspec.yaml (cada app Flutter)
dependencies:
  firebase_crashlytics: ^3.0.0
```

```dart
// main.dart
FlutterError.onError = (errorDetails) {
  FirebaseCrashlytics.instance.recordFlutterFatalError(errorDetails);
};

// Errores async no capturados
PlatformDispatcher.instance.onError = (error, stack) {
  FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
  return true;
};
```

### Grupos de alertas en Crashlytics

```
Firebase Console → Crashlytics → Alertas
→ "Alerta de nuevo problema": Email inmediato cuando aparece un crash nuevo
→ "Alerta de regresión": Si un crash que se marcó como solucionado reaparece
```

---

## Firebase Performance Monitoring

Mide automáticamente:
- Tiempo de inicio de la app (cold / warm start)
- Latencia de requests HTTP
- Render time de pantallas

### Trazas personalizadas

```dart
// Medir tiempo de carga de una inspección
final trace = FirebasePerformance.instance.newTrace('load_inspection');
await trace.start();

try {
  final inspection = await inspectionRepo.get(id);
  trace.putAttribute('has_items', inspection.items.isNotEmpty.toString());
} finally {
  await trace.stop();
}
```

---

## Firebase Analytics — Eventos a implementar

### Portal Cliente (`apps/cliente`)

```dart
// Evento: cliente abrió un informe de inspección
FirebaseAnalytics.instance.logEvent(
  name: 'view_inspection_report',
  parameters: {'token_type': 'qr'},
);

// Evento: cliente respondió presupuesto
FirebaseAnalytics.instance.logEvent(
  name: 'estimate_response',
  parameters: {'decision': 'accepted'},  // o 'rejected'
);
```

### Panel Admin (`apps/web_admin`)

```dart
// Evento: inspección iniciada
FirebaseAnalytics.instance.logEvent(
  name: 'inspection_started',
  parameters: {'template_id': templateId},
);
```

---

## Runbook de incidentes

### Severidad y tiempos de respuesta

| Severidad | Definición | Tiempo de respuesta |
|---|---|---|
| P1 — Crítico | API caído, 0% disponibilidad | 15 min |
| P2 — Alto | Error rate > 10%, degradación severa | 1 hora |
| P3 — Medio | Feature específica fallando | 4 horas |
| P4 — Bajo | Issue cosmético, log de advertencia | Próximo sprint |

### Pasos ante P1 (API caído)

```bash
# 1. Verificar estado del servicio
gcloud run services describe tallerapp-api \
  --region=us-central1 --project=taller-85514

# 2. Ver logs recientes
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --project=taller-85514 --limit=20 --format=json

# 3. Rollback a revisión anterior si el problema es del código
gcloud run services update-traffic tallerapp-api \
  --region=us-central1 --project=taller-85514 \
  --to-revisions=REVISION_ANTERIOR=100

# 4. Si es problema de configuración (secreto incorrecto, etc.)
gcloud run services update tallerapp-api \
  --region=us-central1 --project=taller-85514 \
  [--set-env-vars o --set-secrets según corresponda]
```

---

## Checklist de monitoreo

- [ ] Cloud Monitoring: uptime check creado para `/api/v1/health`
- [ ] Cloud Monitoring: alertas de errores 5xx configuradas
- [ ] Cloud Monitoring: alertas de latencia p95 > 2s configuradas
- [ ] Cloud Monitoring: alerta de instancias al límite configurada
- [ ] Cloud Monitoring: presupuesto de billing con alertas
- [ ] Log-based metric `backend-5xx-errors` creada
- [ ] Sentry DSN configurado en Secret Manager + backend
- [ ] Firebase Crashlytics integrado en apps Flutter
- [ ] Firebase Performance Monitoring integrado en apps Flutter
- [ ] Firebase Analytics integrado en apps Flutter
- [ ] Dashboard personalizado creado en Cloud Monitoring
- [ ] Canal de notificaciones (email) configurado en alertas
