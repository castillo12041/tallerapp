# Desarrollo Local

> Flujo de trabajo diario. Prerrequisito: completar [SETUP.md](SETUP.md) primero.

---

## Resumen rápido

| Tarea | Comando |
|---|---|
| Iniciar backend | `make dev` |
| Iniciar Firebase Emulator | `make emulators` |
| Ejecutar tests | `make test` |
| Lint | `make lint` |
| Build portal cliente | `make build-cliente` |
| Ver todos los comandos | `make help` |

---

## Backend — FastAPI

### Opción A: Nativo (recomendado para desarrollo)

```bash
# Activar virtualenv y arrancar con hot reload
make dev

# O manualmente:
cd backend
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate        # Windows PowerShell
uvicorn app.main:app --reload
```

**URLs:**
- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/api/v1/openapi.json
- Redoc: http://localhost:8000/redoc

El hot reload detecta cambios en `backend/app/` automáticamente.

### Opción B: Docker Compose

```bash
# Construir imagen y arrancar
make build && make up

# Ver logs en tiempo real
make logs

# Detener
make down
```

Con Docker la fuente está montada como volumen — el hot reload funciona igual.

### Variables de entorno en desarrollo

El backend lee `backend/.env`. Cambios en `.env` requieren reiniciar uvicorn.

Para sobreescribir puntualmente sin editar `.env`:

```bash
# Ejemplo: cambiar log level sin modificar .env
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

---

## Firebase Emulator Suite

Usar el emulador en desarrollo permite:
- Tests sin tocar Firestore de producción
- Desarrollo sin internet
- UI visual de datos en tiempo real

### Iniciar emuladores

```bash
# Terminal separada del backend
make emulators

# O directamente:
firebase emulators:start
```

**Servicios y puertos:**

| Servicio | Puerto | URL |
|---|---|---|
| Auth Emulator | 9099 | — |
| Firestore Emulator | 8080 | — |
| Storage Emulator | 9199 | — |
| Hosting Emulator | 5000 | http://localhost:5000 |
| Emulator UI | 4000 | **http://localhost:4000** |

### Conectar el backend al emulador

Para que el backend use el emulador en lugar de Firebase real, agregar a `backend/.env`:

```bash
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
STORAGE_EMULATOR_HOST=localhost:9199
```

> **Nota:** Estas variables son reconocidas por el Firebase Admin SDK automáticamente.
> No requieren cambios en el código del backend.

### Importar datos de seed al emulador

```bash
# Exportar estado actual del emulador (para persistir entre sesiones)
firebase emulators:export ./emulator-data

# Importar al arrancar
firebase emulators:start --import=./emulator-data
```

---

## Flutter — Portal del Cliente (`apps/cliente`)

### Prerrequisito: generar código

Debe ejecutarse UNA VEZ (y después de cambios en modelos Freezed):

```bash
make generate-cliente

# O manualmente:
cd apps/cliente
dart run build_runner build --delete-conflicting-outputs
```

### Correr en Chrome (desarrollo)

```bash
cd apps/cliente
flutter run -d chrome --dart-define-from-file=.dart-defines.json
```

El hot reload en Flutter Web se activa con `r` en la terminal, `R` para hot restart.

### Configurar `apps/cliente/.dart-defines.json`

Copiar desde el ejemplo y completar:

```bash
cp apps/cliente/.dart-defines.example.json apps/cliente/.dart-defines.json
# Editar con los valores reales de Firebase Web
```

Apuntar a backend local:
```json
{
  "API_BASE_URL": "http://localhost:8000",
  "ENVIRONMENT": "development"
}
```

### Build para producción

```bash
make build-cliente
# Output: apps/cliente/build/web/
```

---

## Flutter — App Mobile (`apps/mobile`)

> La app mobile no está implementada aún (Fase 14+). Esta sección es preparatoria.

### Android — Emulador

```bash
# Iniciar emulador Android (desde Android Studio o CLI)
emulator -avd Pixel_7_API_34

# Correr la app
cd apps/mobile
flutter run --dart-define-from-file=.dart-defines.json
```

> En el emulador Android, `localhost` del host es `10.0.2.2`. El `.dart-defines.json` de mobile tiene este valor por defecto.

### Android — Dispositivo físico

```bash
# Ver dispositivos conectados
flutter devices

# Correr en dispositivo específico
flutter run -d <device_id> --dart-define-from-file=.dart-defines.json
```

Para conectar al backend local desde un dispositivo físico, usar la IP de la máquina en la red local:

```json
{
  "API_BASE_URL": "http://192.168.1.x:8000"
}
```

---

## Tests

### Backend

```bash
# Todos los tests
make test

# Con cobertura (genera htmlcov/index.html)
make test-cov

# Un archivo específico
bash scripts/test.sh test_auth

# Un test específico
cd backend && pytest tests/features/test_auth.py::test_login_success -v
```

Los tests usan mocks de Firebase — no requieren el emulador ni credenciales reales.

### Flutter

```bash
cd apps/cliente
flutter test
```

---

## Linting y Calidad

### Backend

```bash
# Verificar (sin modificar)
make lint

# Auto-fix lo que sea automático
make lint-fix

# Solo ruff
cd backend && ruff check .

# Solo mypy (type checking)
cd backend && mypy app/
```

### Flutter

```bash
cd apps/cliente
flutter analyze
dart format --set-exit-if-changed .
```

---

## Flujo de trabajo típico (día a día)

```bash
# Terminal 1 — Backend
make dev

# Terminal 2 — Firebase Emulator (opcional)
make emulators

# Terminal 3 — Flutter Web (cuando trabajas en el portal)
cd apps/cliente && flutter run -d chrome --dart-define-from-file=.dart-defines.json

# Antes de hacer commit
make test
make lint
```

---

## Estructura del proyecto en desarrollo

```
tallerapp/
├── backend/           → FastAPI en :8000
│   ├── app/
│   ├── tests/
│   ├── .env           ← TUS SECRETOS (no committear)
│   └── firebase_credentials.json  ← TUS CREDENCIALES (no committear)
├── apps/
│   ├── cliente/       → Flutter Web en :57627 (chrome)
│   │   └── .dart-defines.json  ← TUS DART-DEFINES (no committear)
│   ├── web_admin/     → (Fase 14+)
│   └── mobile/        → (Fase 14+)
├── infra/
│   └── firebase/      → firestore.rules, indexes, storage.rules
└── firebase.json      → config de hosting y emuladores
```

---

## Resolución de problemas comunes

### Backend no inicia: `ModuleNotFoundError`

```bash
# Verificar que el virtualenv esté activado
which python  # debe apuntar a backend/.venv/bin/python
source backend/.venv/bin/activate
```

### Backend: `FIREBASE_CREDENTIALS_NOT_FOUND`

```bash
# Verificar que el archivo exista
ls backend/firebase_credentials.json

# Verificar que FIREBASE_CREDENTIALS_PATH esté en .env
grep FIREBASE_CREDENTIALS backend/.env
```

### Flutter: `Couldn't connect to localhost:8000`

1. Verificar que el backend esté corriendo: `curl http://localhost:8000/api/v1/health`
2. En Android emulador, cambiar `API_BASE_URL` a `http://10.0.2.2:8000`
3. En dispositivo físico, usar la IP local de tu máquina

### Firestore: `PERMISSION_DENIED`

1. Si usas emulador: verificar que `FIRESTORE_EMULATOR_HOST` esté en `.env`
2. Si usas Firebase real: verificar Firestore Security Rules

### `dart run build_runner` falla con conflictos

```bash
cd apps/cliente
dart run build_runner build --delete-conflicting-outputs
```

### Puerto 8000 ocupado

```bash
# Encontrar el proceso
lsof -i :8000     # Mac/Linux
netstat -ano | findstr :8000  # Windows

# O cambiar el puerto
uvicorn app.main:app --port 8001 --reload
```

---

## Atajos útiles

```bash
# Ver todos los comandos disponibles
make help

# Limpiar todos los artefactos de build
make clean

# Rebuild completo del entorno Python
rm -rf backend/.venv && make setup

# Regenerar código Flutter después de cambios en modelos
make generate-cliente
```
