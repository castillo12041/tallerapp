# Guía de Desarrollo

> Setup, convenciones y flujo de trabajo del proyecto.

## Prerrequisitos

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Flutter SDK | 3.x | `flutter --version` |
| Dart SDK | 3.3+ | incluido con Flutter |
| Python | 3.12 | `python --version` |
| Firebase CLI | latest | `firebase --version` |
| FlutterFire CLI | latest | `flutterfire --version` |
| Git | 2.x | `git --version` |

Instalar Firebase CLI: `npm install -g firebase-tools`
Instalar FlutterFire CLI: `dart pub global activate flutterfire_cli`

---

## Setup inicial

### 1. Firebase

```bash
firebase login
# Crear proyecto en https://console.firebase.google.com o con CLI:
firebase projects:create taller-inspeccion-dev

# En Firebase Console, activar:
# → Authentication > Sign-in method > Email/Password
# → Firestore Database > Create in production mode
# → Storage (Fase 5)

# Descargar credenciales del Admin SDK:
# Console > Configuración del proyecto > Cuentas de servicio >
# Generar nueva clave privada > guardar como backend/firebase_credentials.json
```

### 2. Backend

```bash
cd backend

# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate       # Windows
source venv/bin/activate      # macOS / Linux

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env — completar al menos:
#   FIREBASE_PROJECT_ID
#   FIREBASE_CREDENTIALS_PATH
#   JWT_SECRET_KEY (generar con: openssl rand -hex 32)

# Verificar que arranca
uvicorn app.main:app --reload
# → http://localhost:8000/api/v1/health debe retornar {"status":"healthy"}
```

### 3. Flutter

```bash
cd apps/mobile

# Configurar Firebase para Flutter (genera lib/firebase_options.dart)
flutterfire configure
# Seleccionar el proyecto creado en el paso anterior

# Instalar paquetes
flutter pub get

# Verificar análisis estático
flutter analyze

# Ejecutar tests
flutter test

# Lanzar en dispositivo/emulador
flutter run
```

---

## Generación de código (build_runner)

El proyecto usa `build_runner` para generar:
- `*.g.dart` — serialización JSON (JsonSerializable)
- `*.freezed.dart` — modelos inmutables (Freezed)

```bash
cd apps/mobile

# Generar una vez
dart run build_runner build --delete-conflicting-outputs

# Modo watch (durante desarrollo activo)
dart run build_runner watch --delete-conflicting-outputs
```

Los archivos generados están en `.gitignore`. Siempre regenerar tras un checkout.

---

## Testing

### Backend

```bash
cd backend
pytest                                      # todos los tests
pytest tests/test_main.py                   # archivo específico
pytest --cov=app --cov-report=html          # con cobertura HTML
pytest -v                                   # verbose
```

Cobertura mínima requerida: **80%**

### Flutter

```bash
cd apps/mobile
flutter test                                # todos los tests
flutter test test/features/auth/            # directorio específico
flutter test --coverage                     # genera lcov.info
```

---

## Convenciones de código

### Dart / Flutter

| Elemento | Convención | Ejemplo |
|---|---|---|
| Archivos | `snake_case` | `auth_repository.dart` |
| Clases | `PascalCase` | `AuthRepository` |
| Variables y funciones | `camelCase` | `accessToken`, `getUser()` |
| Constantes | `camelCase` en clase | `AppConstants.apiBaseUrl` |
| Providers | sufijo `Provider` | `authProvider` |
| Notifiers | sufijo `Notifier` | `AuthNotifier` |
| UseCases | sufijo `UseCase` | `LoginUseCase` |
| Páginas | sufijo `Page` | `LoginPage` |
| Widgets reutilizables | descriptivo | `InspectionStatusChip` |

### Python / FastAPI

| Elemento | Convención | Ejemplo |
|---|---|---|
| Archivos | `snake_case` | `auth_router.py` |
| Clases | `PascalCase` | `AuthService`, `UserEntity` |
| Funciones y variables | `snake_case` | `verify_token()`, `access_token` |
| Constantes | `UPPER_SNAKE_CASE` | `JWT_ALGORITHM` |
| Schemas Pydantic request | sufijo `Request` | `LoginRequest` |
| Schemas Pydantic response | sufijo `Response` | `AuthResponse` |
| Entidades de dominio | sufijo `Entity` | `UserEntity` |
| URL de endpoints | kebab-case | `/auth/refresh-token` |

### Estructura de un feature Flutter

```
features/auth/
├── data/
│   ├── datasources/
│   │   └── auth_remote_datasource.dart     # Interface + impl
│   ├── models/
│   │   └── user_model.dart                 # DTO con @freezed
│   └── repositories/
│       └── auth_repository_impl.dart       # Implementación
├── domain/
│   ├── entities/
│   │   └── user.dart                       # Entidad pura Dart
│   ├── repositories/
│   │   └── auth_repository.dart            # Interface abstract
│   └── usecases/
│       ├── login_usecase.dart
│       ├── logout_usecase.dart
│       └── get_current_user_usecase.dart
└── presentation/
    ├── pages/
    │   ├── login_page.dart
    │   ├── register_page.dart
    │   └── forgot_password_page.dart
    ├── providers/
    │   └── auth_provider.dart
    └── widgets/
        └── auth_form_field.dart
```

---

## Límites de archivos

Según las reglas del proyecto (`CLAUDE.md`):

| Límite | Valor |
|---|---|
| Objetivo por archivo | 300 líneas |
| Máximo absoluto | 500 líneas |

Si un archivo supera 500 líneas → dividirlo obligatoriamente.

---

## Git workflow

### Ramas

```
main        ← producción (protegida, requiere PR)
develop     ← integración (base para features)
feat/[nombre]   ← nueva feature
fix/[nombre]    ← corrección de bug
refactor/[nombre] ← refactoring sin cambio de comportamiento
```

### Conventional Commits

```
feat(auth): add login with Firebase Auth
fix(vehicles): correct plate normalization regex
refactor(inspection): extract item scoring logic
test(auth): add refresh token rotation coverage
docs(api): document vehicle search endpoint
chore(deps): update Flutter packages to latest
```

### Checklist antes de commit

```bash
# Backend
ruff check .          # lint
mypy app/             # tipos
pytest                # tests

# Flutter
flutter analyze       # lint + tipos
flutter test          # tests
```

---

## Variables de entorno

Ver `backend/.env.example` para la lista completa con descripción de cada variable.

**Regla:** Nunca hardcodear valores en código. Toda configuración va en variables de entorno.

```bash
# Generar JWT_SECRET_KEY segura
openssl rand -hex 32
```
