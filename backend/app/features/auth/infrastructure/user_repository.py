from __future__ import annotations

from firebase_admin import firestore

from app.features.auth.domain.entities import AuthUser, UserRole


class UserRepository:
    """
    Acceso al documento del usuario en Firestore.

    Estructura en Firestore:
      users/{uid}           — índice global (todos los usuarios, incluido superadmin)
      tenants/{tenantId}/users/{uid}  — datos completos del usuario en un tenant

    El login solo necesita el índice global para obtener tenantId, role y permissions.
    Los datos del perfil completo se leen desde la subcolección del tenant.
    """

    def __init__(self, db: firestore.Client) -> None:
        self._db = db

    def find_by_uid(self, uid: str) -> AuthUser | None:
        """
        Busca el usuario por Firebase UID.
        Retorna None si el usuario no existe o está eliminado (soft delete).
        """
        doc = self._db.collection("users").document(uid).get()
        if not doc.exists:
            return None

        data = doc.to_dict() or {}
        if data.get("deletedAt") is not None:
            return None

        return self._to_entity(data)

    def _to_entity(self, data: dict) -> AuthUser:
        try:
            role = UserRole(data.get("role", "customer"))
        except ValueError:
            role = UserRole.CUSTOMER

        return AuthUser(
            uid=data.get("uid", ""),
            email=data.get("email", ""),
            display_name=data.get("displayName", ""),
            role=role,
            permissions=data.get("permissions", []),
            tenant_id=data.get("tenantId") or None,
            plan=data.get("plan") or None,
            is_active=bool(data.get("isActive", True)),
        )
