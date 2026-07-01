# Instalación desde Cero

> Guía completa para configurar el entorno de desarrollo desde un repositorio vacío.
> Para el flujo de trabajo diario ver: [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)

---

## Prerrequisitos

### Software requerido

| Software | Versión | Instalación |
|---|---|---|
| **Git** | 2.40+ | https://git-scm.com |
| **Python** | 3.12+ | https://python.org |
| **Flutter** | 3.x | https://flutter.dev/docs/get-started/install |
| **Node.js** | 18+ | https://nodejs.org (para Firebase CLI) |
| **Firebase CLI** | latest | `npm install -g firebase-tools` |
| **Google Cloud CLI** | latest | https://cloud.google.com/sdk/docs/install |
| **Docker** | 24+ | https://docs.docker.com/get-docker/ (opcional) |
| **make** | any | `choco install make` (Windows), preinstalado en Mac/Linux |

### En Windows

Se recomienda fuertemente **WSL2** para una experiencia coherente con CI/CD:

```powershell
# Instalar WSL2 con Ubuntu
wsl --install -d Ubuntu

# Luego trabajar desde WSL2 para los scripts bash
```

Alternativa sin WSL2: usar **Git Bash** para los scripts y `make`.

---

## Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/tu-org/tallerapp.git
cd tallerapp
```

---

## Paso 2 — Configurar Firebase

### 2.1 Crear proyecto Firebase (si no existe)

1. Ir a https://console.firebase.google.com
2. Crear proyecto → nombre: `taller-85514`
3. Habilitar Google Analytics (recomendado)

### 2.2 Habilitar servicios Firebase

En Firebase Console, habilitar:

- **Authentication** → Sign-in method → Email/Password ✓
- **Firestore Database** → Modo producción (las rules están en `infra/firebase/`)
- **Storage** → Modo producción
- **Hosting** → Configurar después

### 2.3 Descargar Service Account (para el backend)

```
Firebase Console
  → Configuración del proyecto (ícono ⚙️)
  → Cuentas de servicio
  → "Generar nueva clave privada"
  → Guardar como: backend/firebase_credentials.json
```

> ⚠️ **NUNCA commitear este archivo.** Está en `.gitignore`.

### 2.4 Login en Firebase CLI

```bash
firebase login
firebase use taller-85514
```

---

## Paso 3 — Configurar Google Cloud

### 3.1 Login en gcloud

```bash
gcloud auth login
gcloud config set project taller-85514
```

### 3.2 Habilitar APIs necesarias

```bash
gcloud services enable \
  firestore.googleapis.com \
  firebase.googleapis.com \
  storage.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

> Esto tarda 1-2 minutos. Ver detalles en [GOOGLE_CLOUD.md](GOOGLE_CLOUD.md).

---

## Paso 4 — Setup automático

```bash
# Instala dependencias, crea .env con claves generadas, configura Flutter
make setup
```

El script `scripts/setup.sh`:
1. Verifica prerrequisitos (Python 3.12+, Flutter, Firebase CLI)
2. Crea `backend/.venv` e instala dependencias Python
3. Copia `backend/.env.example` → `backend/.env` con claves JWT y HMAC generadas
4. Copia `apps/cliente/.dart-defines.example.json` → `apps/cliente/.dart-defines.json`
5. Ejecuta `flutter pub get` en apps/cliente

---

## Paso 5 — Completar configuración manual

### 5.1 Completar `backend/.env`

Abrir `backend/.env` y verificar/completar:

```bash
# Estos son los únicos valores que requieren acción manual en desarrollo:
FIREBASE_PROJECT_ID=taller-85514          # Ya configurado
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json  # Ya configurado
FIREBASE_STORAGE_BUCKET=taller-85514.appspot.com     # Ya configurado

# JWT_SECRET_KEY y HMAC_SECRET_KEY ya fueron generados por make setup
# Verificar que no sean el valor de ejemplo:
grep JWT_SECRET_KEY backend/.env
```

### 5.2 Completar `apps/cliente/.dart-defines.json`

Obtener los valores de Firebase Web:

```
Firebase Console → Configuración → Tus apps → Web
→ "Agregar app" si no existe, o copiar configuración existente
```

Editar `apps/cliente/.dart-defines.json`:
```json
{
  "API_BASE_URL": "http://localhost:8000",
  "ENVIRONMENT": "development",
  "APP_VERSION": "1.0.0",
  "FIREBASE_API_KEY": "AIza...",
  "FIREBASE_AUTH_DOMAIN": "taller-85514.firebaseapp.com",
  "FIREBASE_PROJECT_ID": "taller-85514",
  "FIREBASE_STORAGE_BUCKET": "taller-85514.appspot.com",
  "FIREBASE_MESSAGING_SENDER_ID": "123456789",
  "FIREBASE_APP_ID": "1:123456789:web:abc...",
  "FIREBASE_MEASUREMENT_ID": "G-..."
}
```

---

## Paso 6 — Desplegar Firestore Rules e índices

```bash
# Deploy de rules e índices (requiere firebase login)
firebase deploy --only firestore:rules,firestore:indexes,storage

# Para solo reglas:
firebase deploy --only firestore:rules
```

---

## Paso 7 — Generar código Flutter

```bash
# Genera .freezed.dart y .g.dart para apps/cliente
make generate-cliente
```

---

## Paso 8 — Crear usuario inicial

```bash
# Crea SuperAdmin en Firebase Auth + Firestore + planes por defecto
make seed
```

El script pedirá email, contraseña y nombre. Usar credenciales que recuerdes para el primer login.

---

## Paso 9 — Verificar instalación

### Backend

```bash
make dev
# Abrir en otro terminal:
curl http://localhost:8000/api/v1/health
# Respuesta esperada: {"status": "ok", ...}
```

### Firebase Emulator (opcional para testing)

```bash
# En otra terminal
make emulators
# UI del emulador: http://localhost:4000
```

### Flutter Web — Portal Cliente

```bash
cd apps/cliente
flutter run -d chrome --dart-define-from-file=.dart-defines.json
```

---

## Verificación final

```bash
make test        # 233+ tests deben pasar
make lint        # Sin errores de lint
```

---

## Problemas comunes

### `firebase_credentials.json: No such file`
→ Descargar desde Firebase Console y guardar en `backend/firebase_credentials.json`

### `PERMISSION_DENIED` en Firestore
→ Verificar que el Service Account tenga rol **Cloud Datastore User** en IAM

### Tests fallan con `FIREBASE_PROJECT_ID not set`
→ El backend tiene mocks para tests — no requiere Firebase real. Ver `backend/tests/conftest.py`

### Flutter error `String.fromEnvironment` vacío
→ Dart-defines no pasan en `flutter run` sin el flag `--dart-define-from-file`

### `make: command not found` en Windows
→ Usar WSL2, o ejecutar comandos directamente: `cd backend && python -m pytest tests/`

---

## Siguientes pasos

Una vez instalado y verificado:

1. Ver [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) — flujo de trabajo diario
2. Ver [GOOGLE_CLOUD.md](GOOGLE_CLOUD.md) — configuración completa de GCP
3. Ver [DEPLOYMENT.md](DEPLOYMENT.md) — cómo desplegar a producción
