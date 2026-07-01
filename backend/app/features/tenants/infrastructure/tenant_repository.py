from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.features.tenants.domain.entities import Tenant

_FIELD_MAP: dict[str, str] = {
    "name": "name",
    "plan_id": "planId",
    "is_active": "isActive",
    "is_suspended": "isSuspended",
}


class TenantRepository:
    _COLLECTION = "tenants"

    def __init__(self, db: firestore.Client) -> None:
        self._db = db

    def create(self, tenant: Tenant) -> None:
        doc_ref = self._db.collection(self._COLLECTION).document(tenant.id)
        doc_ref.set(self._to_firestore(tenant))

    def find_by_id(self, tenant_id: str) -> Tenant | None:
        doc = self._db.collection(self._COLLECTION).document(tenant_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("deletedAt") is not None:
            return None
        return self._to_entity(doc.id, data)

    def find_by_slug(self, slug: str) -> Tenant | None:
        docs = (
            self._db.collection(self._COLLECTION)
            .where("slug", "==", slug)
            .limit(1)
            .stream()
        )
        for doc in docs:
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                return self._to_entity(doc.id, data)
        return None

    def update(self, tenant_id: str, fields: dict, updated_by: str) -> None:
        firestore_data: dict = {
            _FIELD_MAP[k]: v
            for k, v in fields.items()
            if k in _FIELD_MAP
        }
        firestore_data["updatedAt"] = datetime.now(timezone.utc)
        firestore_data["updatedBy"] = updated_by
        self._db.collection(self._COLLECTION).document(tenant_id).update(firestore_data)

    def list_all(self) -> list[Tenant]:
        docs = self._db.collection(self._COLLECTION).stream()
        return [
            self._to_entity(doc.id, doc.to_dict())
            for doc in docs
            if doc.to_dict().get("deletedAt") is None
        ]

    # ------------------------------------------------------------------

    def _to_firestore(self, tenant: Tenant) -> dict:
        return {
            "name": tenant.name,
            "slug": tenant.slug,
            "rut": tenant.rut,
            "planId": tenant.plan_id,
            "subscriptionId": tenant.subscription_id,
            "subscriptionStatus": tenant.subscription_status,
            "isActive": tenant.is_active,
            "isSuspended": tenant.is_suspended,
            "storageUsedBytes": tenant.storage_used_bytes,
            "inspectionCountThisMonth": tenant.inspection_count_this_month,
            "activeUserCount": tenant.active_user_count,
            "tenantId": tenant.tenant_id,
            "createdAt": tenant.created_at,
            "updatedAt": tenant.updated_at,
            "createdBy": tenant.created_by,
            "updatedBy": tenant.updated_by,
            "deletedAt": tenant.deleted_at,
        }

    def _to_entity(self, doc_id: str, data: dict) -> Tenant:
        def _dt(value: object) -> datetime:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value
            raise ValueError(f"Expected datetime, got {type(value)}")

        return Tenant(
            id=doc_id,
            name=data["name"],
            slug=data["slug"],
            rut=data.get("rut", ""),
            plan_id=data.get("planId", "basic"),
            subscription_id=data.get("subscriptionId"),
            subscription_status=data.get("subscriptionStatus", "trialing"),
            is_active=data.get("isActive", True),
            is_suspended=data.get("isSuspended", False),
            storage_used_bytes=data.get("storageUsedBytes", 0),
            inspection_count_this_month=data.get("inspectionCountThisMonth", 0),
            active_user_count=data.get("activeUserCount", 0),
            tenant_id=data.get("tenantId", doc_id),
            created_at=_dt(data["createdAt"]),
            updated_at=_dt(data["updatedAt"]),
            created_by=data.get("createdBy", ""),
            updated_by=data.get("updatedBy", ""),
            deleted_at=data.get("deletedAt"),
        )
