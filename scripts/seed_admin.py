#!/usr/bin/env python3
"""
seed_admin.py — Crea el usuario SuperAdmin inicial y la configuración base.

Uso: python scripts/seed_admin.py
     make seed

Requisitos:
  - backend/.env configurado con Firebase credentials
  - backend/firebase_credentials.json disponible
  - Correr desde la raíz del proyecto

Crea:
  - Usuario en Firebase Auth
  - Documento en Firestore: users/{uid}
  - Documento en Firestore: tenants/platform (tenant de la plataforma)
  - Colección: plans/ con los planes por defecto
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Ajustar path para importar desde backend
ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Cargar .env antes de importar settings
from dotenv import load_dotenv  # type: ignore[import]
load_dotenv(BACKEND / ".env")

try:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore
except ImportError:
    print("ERROR: firebase-admin no instalado.")
    print("Activar virtualenv: source backend/.venv/bin/activate")
    sys.exit(1)


# ----------------------------------------------------------------
# Inicializar Firebase
# ----------------------------------------------------------------
CREDS_PATH = BACKEND / "firebase_credentials.json"
if not CREDS_PATH.exists():
    print(f"ERROR: {CREDS_PATH} no encontrado.")
    print("Descargar desde Firebase Console → Configuración → Cuentas de servicio")
    sys.exit(1)

cred = credentials.Certificate(str(CREDS_PATH))
firebase_admin.initialize_app(cred, {"projectId": os.getenv("FIREBASE_PROJECT_ID", "taller-85514")})
db = firestore.client()


# ----------------------------------------------------------------
# Datos del SuperAdmin
# ----------------------------------------------------------------
def prompt(label: str, default: str = "") -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value if value else default


def now() -> datetime:
    return datetime.now(UTC)


def seed_platform_tenant() -> str:
    """Crea el tenant de la plataforma (id fijo: 'platform')."""
    tenant_id = "platform"
    ref = db.collection("tenants").document(tenant_id)
    if ref.get().exists:
        print(f"  ✓ Tenant 'platform' ya existe — omitiendo")
        return tenant_id

    ref.set({
        "id": tenant_id,
        "name": "Taller Inspección — Platform",
        "plan": "enterprise",
        "status": "active",
        "isSystem": True,
        "createdAt": now(),
        "updatedAt": now(),
        "createdBy": "system",
        "updatedBy": "system",
        "settings": {
            "timezone": "America/Santiago",
            "locale": "es-CL",
            "currency": "CLP",
        },
    })
    print(f"  ✓ Tenant 'platform' creado")
    return tenant_id


def seed_plans() -> None:
    """Crea los planes SaaS por defecto."""
    plans = [
        {
            "id": "starter",
            "name": "Starter",
            "price": 0,
            "currency": "CLP",
            "maxUsers": 2,
            "maxInspectionsPerMonth": 50,
            "features": ["inspections", "clients", "vehicles", "pdf", "qr"],
            "isActive": True,
        },
        {
            "id": "professional",
            "name": "Professional",
            "price": 29900,
            "currency": "CLP",
            "maxUsers": 10,
            "maxInspectionsPerMonth": 500,
            "features": ["inspections", "clients", "vehicles", "pdf", "qr",
                         "estimates", "work_orders", "analytics", "email_notifications"],
            "isActive": True,
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "price": 99900,
            "currency": "CLP",
            "maxUsers": -1,  # ilimitado
            "maxInspectionsPerMonth": -1,
            "features": ["inspections", "clients", "vehicles", "pdf", "qr",
                         "estimates", "work_orders", "analytics", "email_notifications",
                         "whatsapp_notifications", "api_access", "custom_domain",
                         "priority_support", "ai_features"],
            "isActive": True,
        },
    ]

    batch = db.batch()
    for plan in plans:
        ref = db.collection("plans").document(plan["id"])
        if not ref.get().exists:
            plan["createdAt"] = now()
            plan["updatedAt"] = now()
            batch.set(ref, plan)
            print(f"  ✓ Plan '{plan['name']}' creado")
        else:
            print(f"  ✓ Plan '{plan['name']}' ya existe — omitiendo")

    batch.commit()


def seed_super_admin(email: str, password: str, display_name: str, tenant_id: str) -> str:
    """Crea el usuario SuperAdmin en Firebase Auth + Firestore."""
    # Crear en Firebase Auth
    try:
        user = auth.get_user_by_email(email)
        print(f"  ✓ Usuario {email} ya existe en Firebase Auth (uid: {user.uid})")
        uid = user.uid
    except auth.UserNotFoundError:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=True,
        )
        uid = user.uid
        print(f"  ✓ Usuario creado en Firebase Auth (uid: {uid})")

    # Establecer custom claims
    auth.set_custom_user_claims(uid, {
        "role": "superadmin",
        "tenantId": tenant_id,
        "plan": "enterprise",
    })
    print(f"  ✓ Custom claims establecidos (role: superadmin)")

    # Crear documento en Firestore
    user_ref = db.collection("users").document(uid)
    if not user_ref.get().exists:
        user_ref.set({
            "id": uid,
            "uid": uid,
            "tenantId": tenant_id,
            "email": email,
            "displayName": display_name,
            "role": "superadmin",
            "status": "active",
            "permissions": [],  # superadmin tiene todos los permisos implícitamente
            "createdAt": now(),
            "updatedAt": now(),
            "createdBy": "system",
            "updatedBy": "system",
        })
        print(f"  ✓ Documento users/{uid} creado en Firestore")
    else:
        print(f"  ✓ Documento users/{uid} ya existe — omitiendo")

    return uid


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
def main() -> None:
    print()
    print("  Taller Inspección — Seed de datos iniciales")
    print("  ============================================")
    print()

    # Recopilar datos del superadmin
    print("  Configuración del SuperAdmin:")
    email = prompt("    Email", "admin@tallerinspeccion.cl")
    password = prompt("    Password (min 8 chars)", "Cambiar123!")
    display_name = prompt("    Nombre completo", "Super Admin")

    if len(password) < 8:
        print("ERROR: La contraseña debe tener al menos 8 caracteres")
        sys.exit(1)

    print()
    print("  Creando tenant de plataforma...")
    tenant_id = seed_platform_tenant()

    print()
    print("  Creando planes SaaS...")
    seed_plans()

    print()
    print("  Creando usuario SuperAdmin...")
    uid = seed_super_admin(email, password, display_name, tenant_id)

    print()
    print("  ✓ Seed completado")
    print("  ==================")
    print()
    print(f"    Email:   {email}")
    print(f"    UID:     {uid}")
    print(f"    Rol:     superadmin")
    print(f"    Tenant:  {tenant_id}")
    print()
    print("  IMPORTANTE: Cambiar la contraseña en producción.")
    print()


if __name__ == "__main__":
    main()
