from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.features.users.domain.entities import User

_FIELD_MAP: dict[str, str] = {
    "display_name": "displayName",
    "first_name": "firstName",
    "last_name": "lastName",
    "role": "role",
    "permissions": "permissions",
    "phone": "phone",
    "is_active": "isActive",
}


class UserCrudRepository:
    _COLLECTION = "users"

    def __init__(self, db: firestore.Client) -> None:
        self._db = db

    def create(self, user: User) -> None:
        self._db.collection(self._COLLECTION).document(user.uid).set(
            self._to_firestore(user)
        )

    def find_by_uid(self, uid: str) -> User | None:
        doc = self._db.collection(self._COLLECTION).document(uid).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("deletedAt") is not None:
            return None
        return self._to_entity(doc.id, data)

    def find_by_uid_in_tenant(self, uid: str, tenant_id: str) -> User | None:
        doc = self._db.collection(self._COLLECTION).document(uid).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("deletedAt") is not None:
            return None
        if data.get("tenantId") != tenant_id:
            return None
        return self._to_entity(doc.id, data)

    def list_by_tenant(self, tenant_id: str) -> list[User]:
        docs = (
            self._db.collection(self._COLLECTION)
            .where("tenantId", "==", tenant_id)
            .stream()
        )
        return [
            self._to_entity(doc.id, doc.to_dict())
            for doc in docs
            if doc.to_dict().get("deletedAt") is None
        ]

    def update(self, uid: str, fields: dict, updated_by: str) -> None:
        firestore_data: dict = {
            _FIELD_MAP[k]: v
            for k, v in fields.items()
            if k in _FIELD_MAP
        }
        firestore_data["updatedAt"] = datetime.now(timezone.utc)
        firestore_data["updatedBy"] = updated_by
        self._db.collection(self._COLLECTION).document(uid).update(firestore_data)

    def deactivate(self, uid: str, deactivated_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(self._COLLECTION).document(uid).update({
            "deletedAt": now,
            "isActive": False,
            "updatedAt": now,
            "updatedBy": deactivated_by,
        })

    # ------------------------------------------------------------------

    def _to_firestore(self, user: User) -> dict:
        return {
            "tenantId": user.tenant_id,
            "email": user.email,
            "displayName": user.display_name,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "role": user.role,
            "permissions": list(user.permissions),
            "plan": user.plan,
            "isActive": user.is_active,
            "phone": user.phone,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
            "createdBy": user.created_by,
            "updatedBy": user.updated_by,
            "deletedAt": user.deleted_at,
        }

    def _to_entity(self, uid: str, data: dict) -> User:
        def _dt(value: object) -> datetime:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value
            raise ValueError(f"Expected datetime, got {type(value)}")

        return User(
            uid=uid,
            email=data.get("email", ""),
            display_name=data.get("displayName", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            role=data.get("role", "customer"),
            permissions=data.get("permissions", []),
            tenant_id=data.get("tenantId", ""),
            plan=data.get("plan"),
            is_active=data.get("isActive", True),
            phone=data.get("phone"),
            created_at=_dt(data["createdAt"]),
            updated_at=_dt(data["updatedAt"]),
            created_by=data.get("createdBy", ""),
            updated_by=data.get("updatedBy", ""),
            deleted_at=data.get("deletedAt"),
        )
