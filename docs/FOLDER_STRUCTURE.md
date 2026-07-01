# Estructura de Carpetas — Monorepo Completo

> Fuente oficial de la organización del código.
> Cada sección indica en qué Fase se implementa.

---

## Raíz del Monorepo

```
tallerapp/
├── apps/                  # Aplicaciones Flutter
│   ├── mobile/            # Android + iOS + PWA (Offline-First)
│   ├── web_admin/         # Flutter Web: /admin + /app
│   └── web_client/        # Flutter Web: /cliente + /informe + /presupuesto
├── backend/               # Servicios Python
│   ├── api/               # FastAPI principal
│   ├── workers/           # Background tasks
│   ├── notifications/     # Dispatcher multicanal
│   ├── pdf_service/       # Generación de PDF
│   └── integrations/      # Adaptadores externos
├── packages/              # Dart/Flutter packages compartidos
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── shared_models/
│   ├── shared_widgets/
│   ├── shared_theme/
│   └── shared_utils/
├── docs/                  # Documentación técnica (fuente oficial)
├── infra/                 # Docker, CI/CD, Cloud Run configs
│   ├── docker/
│   ├── github/
│   └── firebase/
├── scripts/               # Scripts de automatización
└── .github/
    └── workflows/         # GitHub Actions CI/CD
```

---

## apps/mobile/ — App de Campo (Fase 5+)

```
apps/mobile/
├── lib/
│   ├── main.dart
│   ├── main_dev.dart          # Entrypoint desarrollo
│   ├── main_staging.dart      # Entrypoint staging
│   ├── core/
│   │   ├── config/
│   │   │   ├── app_config.dart
│   │   │   └── environment.dart
│   │   ├── constants/
│   │   │   ├── app_constants.dart
│   │   │   ├── route_constants.dart
│   │   │   └── permission_constants.dart
│   │   ├── errors/
│   │   │   ├── app_exception.dart
│   │   │   ├── failure.dart
│   │   │   └── error_handler.dart
│   │   ├── network/
│   │   │   ├── dio_client.dart
│   │   │   └── interceptors/
│   │   │       ├── auth_interceptor.dart
│   │   │       ├── logging_interceptor.dart
│   │   │       └── retry_interceptor.dart
│   │   ├── router/
│   │   │   ├── app_router.dart
│   │   │   ├── routes.dart
│   │   │   └── guards/
│   │   │       ├── auth_guard.dart
│   │   │       ├── permission_guard.dart
│   │   │       └── plan_guard.dart
│   │   ├── storage/
│   │   │   ├── secure_storage.dart
│   │   │   ├── local_database.dart       # Drift entry point
│   │   │   ├── sync_manager.dart         # Offline sync
│   │   │   └── sync_queue.dart           # Queue de operaciones pendientes
│   │   ├── connectivity/
│   │   │   └── connectivity_service.dart
│   │   └── permissions/
│   │       └── permission_checker.dart
│   │
│   └── features/
│       ├── auth/
│       │   ├── data/
│       │   │   ├── datasources/
│       │   │   │   └── auth_remote_datasource.dart
│       │   │   ├── models/
│       │   │   │   └── user_model.dart
│       │   │   └── repositories/
│       │   │       └── auth_repository_impl.dart
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   └── user.dart
│       │   │   ├── repositories/
│       │   │   │   └── auth_repository.dart
│       │   │   └── usecases/
│       │   │       ├── login_usecase.dart
│       │   │       ├── logout_usecase.dart
│       │   │       └── refresh_token_usecase.dart
│       │   └── presentation/
│       │       ├── pages/
│       │       │   ├── login_page.dart
│       │       │   ├── register_page.dart
│       │       │   └── forgot_password_page.dart
│       │       ├── providers/
│       │       │   └── auth_provider.dart
│       │       └── widgets/
│       │           └── auth_form_field.dart
│       │
│       ├── inspection/         # Feature más complejo (Offline-First)
│       │   ├── data/
│       │   │   ├── datasources/
│       │   │   │   ├── inspection_remote_datasource.dart
│       │   │   │   └── inspection_local_datasource.dart    # Drift
│       │   │   ├── models/
│       │   │   │   ├── inspection_model.dart
│       │   │   │   └── inspection_item_model.dart
│       │   │   └── repositories/
│       │   │       └── inspection_repository_impl.dart
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── inspection.dart
│       │   │   │   └── inspection_item.dart
│       │   │   ├── repositories/
│       │   │   │   └── inspection_repository.dart
│       │   │   └── usecases/
│       │   │       ├── create_inspection_usecase.dart
│       │   │       ├── update_item_usecase.dart
│       │   │       ├── complete_inspection_usecase.dart
│       │   │       └── sync_inspection_usecase.dart
│       │   └── presentation/
│       │       ├── pages/
│       │       │   ├── inspection_list_page.dart
│       │       │   ├── inspection_form_page.dart
│       │       │   ├── inspection_detail_page.dart
│       │       │   └── inspection_item_page.dart
│       │       ├── providers/
│       │       │   ├── inspection_provider.dart
│       │       │   └── sync_status_provider.dart
│       │       └── widgets/
│       │           ├── item_status_button.dart
│       │           ├── photo_capture_widget.dart
│       │           ├── audio_recorder_widget.dart
│       │           └── signature_pad_widget.dart
│       │
│       ├── vehicle/            # (mismo patrón)
│       ├── client/
│       ├── estimate/
│       ├── work_order/
│       ├── calendar/
│       ├── dashboard/
│       ├── notification/
│       ├── settings/
│       └── subscription/
│
├── test/
│   ├── unit/
│   │   └── features/
│   ├── widget/
│   └── integration/
├── pubspec.yaml
└── analysis_options.yaml
```

---

## apps/web_admin/ y apps/web_client/ (Fase 6+)

Misma estructura interna que `mobile/`, pero sin el módulo offline/sync. Las páginas y widgets son distintos (diseño web responsive).

---

## backend/api/ — FastAPI Principal (Fase 3+)

```
backend/api/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── middleware/
│   │       ├── auth.py
│   │       ├── tenant.py
│   │       ├── rate_limit.py
│   │       ├── plan.py
│   │       ├── rbac.py
│   │       ├── audit.py
│   │       └── security_headers.py
│   ├── dependencies/
│   │   ├── auth.py              # get_current_user
│   │   ├── tenant.py            # get_tenant_context
│   │   └── permissions.py       # require_permission(), require_plan_feature()
│   │
│   ├── modules/                 # Vertical Slice por bounded context
│   │   ├── identity/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   └── user.py
│   │   │   │   ├── repositories.py
│   │   │   │   └── value_objects/
│   │   │   │       └── email.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   └── login_command.py
│   │   │   │   ├── queries/
│   │   │   │   │   └── get_user_query.py
│   │   │   │   └── services/
│   │   │   │       └── auth_service.py
│   │   │   ├── infrastructure/
│   │   │   │   └── firestore_user_repository.py
│   │   │   └── api/
│   │   │       ├── router.py
│   │   │       └── schemas.py
│   │   │
│   │   ├── tenant/              # (mismo patrón)
│   │   ├── vehicle/
│   │   ├── client/
│   │   ├── inspection/
│   │   ├── document/
│   │   ├── commercial/
│   │   ├── calendar/
│   │   ├── communication/
│   │   ├── analytics/
│   │   ├── audit/
│   │   ├── billing/
│   │   └── storage/
│   │
│   └── infrastructure/
│       ├── firebase/
│       │   ├── client.py        # Firebase Admin SDK init
│       │   └── storage.py
│       └── cache/
│           └── redis_client.py  # Opcional: caché de permisos
│
├── api/
│   ├── v1/
│   │   └── router.py            # Agrega todos los módulos
│   └── v2/
│       └── router.py
│
├── tests/
│   ├── unit/
│   │   └── modules/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

## backend/workers/, notifications/, pdf_service/, integrations/

```
backend/workers/
├── app/
│   ├── main.py
│   └── tasks/
│       ├── pdf_task.py
│       ├── email_task.py
│       ├── whatsapp_task.py
│       └── analytics_task.py

backend/notifications/
├── app/
│   ├── main.py
│   └── handlers/
│       ├── email_handler.py
│       ├── push_handler.py
│       └── whatsapp_handler.py

backend/pdf_service/
├── app/
│   ├── main.py
│   ├── generators/
│   │   ├── inspection_pdf.py
│   │   └── estimate_pdf.py
│   └── templates/
│       ├── inspection.html
│       ├── estimate.html
│       └── work_order.html

backend/integrations/
├── app/
│   ├── main.py
│   └── adapters/
│       ├── plate_api.py
│       └── sendgrid.py
```

---

## packages/ — Dart Compartido

```
packages/
├── domain/
│   └── lib/
│       ├── entities/          # Puro Dart, sin Flutter
│       ├── repositories/      # Interfaces abstractas
│       └── value_objects/     # Email, Plate, Money, Phone
│
├── application/
│   └── lib/
│       ├── commands/          # CreateInspectionCommand, etc.
│       ├── queries/           # GetInspectionQuery, etc.
│       └── use_cases/         # Implementaciones de casos de uso
│
├── infrastructure/
│   └── lib/
│       ├── firebase/
│       ├── dio/
│       └── secure_storage/
│
├── shared_models/
│   └── lib/
│       ├── inspection/        # InspectionModel, InspectionItemModel
│       ├── vehicle/
│       └── user/
│
├── shared_widgets/
│   └── lib/
│       ├── buttons/
│       ├── cards/
│       ├── dialogs/
│       ├── forms/
│       ├── loading/
│       └── empty_states/
│
├── shared_theme/
│   └── lib/
│       ├── app_theme.dart
│       ├── dynamic_theme.dart
│       └── color_scheme.dart
│
└── shared_utils/
    └── lib/
        ├── validators.dart
        ├── date_utils.dart
        ├── string_utils.dart
        └── plate_utils.dart
```

---

## infra/ — Infraestructura

```
infra/
├── docker/
│   ├── api.Dockerfile
│   ├── workers.Dockerfile
│   ├── pdf_service.Dockerfile
│   └── docker-compose.yml
├── firebase/
│   ├── firebase.json           # Firebase Hosting config
│   ├── firestore.rules         # Security Rules
│   ├── firestore.indexes.json  # Índices compuestos
│   └── storage.rules           # Storage Security Rules
└── github/
    └── workflows/
        ├── ci.yml
        ├── deploy-api.yml
        ├── deploy-mobile.yml
        └── deploy-web.yml
```
