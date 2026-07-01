from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.features.clients.domain.entities import Client

_FIELD_MAP: dict[str, str] = {
    "first_name": "firstName",
    "last_name": "lastName",
    "full_name": "fullName",
    "email": "email",
    "phone": "phone",
    "whatsapp": "whatsapp",
    "rut": "rut",
    "vehicle_count": "vehicleCount",
    "inspection_count": "inspectionCount",
    "total_spent": "totalSpent",
    "last_interaction_at": "lastInteractionAt",
}


class ClientRepository:
    _COLLECTION = "clients"

    def __init__(self, db: firestore.Client) -> None:
        self._db = db

    def create(self, client: Client) -> None:
        self._db.collection(self._COLLECTION).document(client.id).set(
            self._to_firestore(client)
        )

    def find_by_id(self, client_id: str, tenant_id: str) -> Client | None:
        doc = self._db.collection(self._COLLECTION).document(client_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("deletedAt") is not None:
            return None
        if data.get("tenantId") != tenant_id:
            return None
        return self._to_entity(doc.id, data)

    def list_by_tenant(self, tenant_id: str, search: str | None = None) -> list[Client]:
        docs = (
            self._db.collection(self._COLLECTION)
            .where("tenantId", "==", tenant_id)
            .stream()
        )
        clients = [
            self._to_entity(doc.id, doc.to_dict())
            for doc in docs
            if doc.to_dict().get("deletedAt") is None
        ]
        if search:
            term = search.lower()
            clients = [
                c for c in clients
                if term in c.full_name.lower()
                or (c.email and term in c.email.lower())
                or (c.rut and term in c.rut.lower())
                or (c.phone and term in c.phone)
            ]
        return clients

    def update(self, client_id: str, tenant_id: str, fields: dict, updated_by: str) -> None:
        firestore_data: dict = {
            _FIELD_MAP[k]: v
            for k, v in fields.items()
            if k in _FIELD_MAP
        }
        firestore_data["updatedAt"] = datetime.now(timezone.utc)
        firestore_data["updatedBy"] = updated_by
        self._db.collection(self._COLLECTION).document(client_id).update(firestore_data)

    def soft_delete(self, client_id: str, tenant_id: str, deleted_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(self._COLLECTION).document(client_id).update({
            "deletedAt": now,
            "updatedAt": now,
            "updatedBy": deleted_by,
        })

    def increment_vehicle_count(self, client_id: str) -> None:
        ref = self._db.collection(self._COLLECTION).document(client_id)
        ref.update({"vehicleCount": firestore.Increment(1)})

    # ------------------------------------------------------------------

    def _to_firestore(self, client: Client) -> dict:
        return {
            "tenantId": client.tenant_id,
            "firstName": client.first_name,
            "lastName": client.last_name,
            "fullName": client.full_name,
            "email": client.email,
            "phone": client.phone,
            "whatsapp": client.whatsapp,
            "rut": client.rut,
            "vehicleCount": client.vehicle_count,
            "inspectionCount": client.inspection_count,
            "totalSpent": client.total_spent,
            "lastInteractionAt": client.last_interaction_at,
            "createdAt": client.created_at,
            "updatedAt": client.updated_at,
            "createdBy": client.created_by,
            "updatedBy": client.updated_by,
            "deletedAt": client.deleted_at,
        }

    def _to_entity(self, doc_id: str, data: dict) -> Client:
        def _dt(v: object) -> datetime:
            if isinstance(v, datetime):
                return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            raise ValueError(f"Expected datetime, got {type(v)}")

        def _dt_opt(v: object) -> datetime | None:
            if v is None:
                return None
            return _dt(v)

        return Client(
            id=doc_id,
            tenant_id=data["tenantId"],
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            full_name=data.get("fullName", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            whatsapp=data.get("whatsapp"),
            rut=data.get("rut"),
            vehicle_count=data.get("vehicleCount", 0),
            inspection_count=data.get("inspectionCount", 0),
            total_spent=data.get("totalSpent", 0.0),
            last_interaction_at=_dt_opt(data.get("lastInteractionAt")),
            created_at=_dt(data["createdAt"]),
            updated_at=_dt(data["updatedAt"]),
            created_by=data.get("createdBy", ""),
            updated_by=data.get("updatedBy", ""),
            deleted_at=_dt_opt(data.get("deletedAt")),
        )
