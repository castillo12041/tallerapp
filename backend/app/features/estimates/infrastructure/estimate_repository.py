from __future__ import annotations

from datetime import datetime, timezone

from app.features.estimates.domain.entities import Estimate
from app.features.inspections.domain.entities import ClientSnapshot, VehicleSnapshot

_COL = "estimates"

_UPDATABLE: dict[str, str] = {
    "notes": "notes",
    "tax_rate": "taxRate",
    "valid_until": "validUntil",
    "status": "status",
    "client_notes": "clientNotes",
    "public_token_id": "publicTokenId",
    "sent_at": "sentAt",
    "viewed_at": "viewedAt",
    "responded_at": "respondedAt",
    "items_count": "itemsCount",
    "subtotal": "subtotal",
    "tax_amount": "taxAmount",
    "total": "total",
}


def _snap_v(data: dict) -> VehicleSnapshot:
    s = data.get("vehicleSnapshot") or {}
    return VehicleSnapshot(
        id=s.get("id", ""),
        plate=s.get("plate", ""),
        make=s.get("make", ""),
        model=s.get("model", ""),
        year=s.get("year"),
        color=s.get("color"),
        vin=s.get("vin"),
    )


def _snap_c(data: dict) -> ClientSnapshot | None:
    s = data.get("clientSnapshot")
    if not s:
        return None
    return ClientSnapshot(
        id=s.get("id", ""),
        full_name=s.get("fullName", ""),
        email=s.get("email"),
        phone=s.get("phone"),
        rut=s.get("rut"),
    )


def _to_entity(data: dict, doc_id: str) -> Estimate:
    return Estimate(
        id=doc_id,
        tenant_id=data["tenantId"],
        number=data["number"],
        status=data["status"],
        inspection_id=data.get("inspectionId"),
        vehicle_snapshot=_snap_v(data),
        client_snapshot=_snap_c(data),
        items_count=data.get("itemsCount", 0),
        subtotal=data.get("subtotal", 0.0),
        tax_rate=data.get("taxRate", 0.0),
        tax_amount=data.get("taxAmount", 0.0),
        total=data.get("total", 0.0),
        currency=data.get("currency", "CLP"),
        notes=data.get("notes"),
        client_notes=data.get("clientNotes"),
        public_token_id=data.get("publicTokenId"),
        valid_until=data.get("validUntil"),
        sent_at=data.get("sentAt"),
        viewed_at=data.get("viewedAt"),
        responded_at=data.get("respondedAt"),
        deleted_at=data.get("deletedAt"),
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
        created_by=data["createdBy"],
        updated_by=data["updatedBy"],
    )


class EstimateRepository:
    def __init__(self, db: object) -> None:
        self._db = db

    def create(self, data: dict) -> None:
        doc_id = data["id"]
        self._db.collection(_COL).document(doc_id).set(data)  # type: ignore[union-attr]

    def find_by_id(self, estimate_id: str, tenant_id: str) -> Estimate | None:
        doc = self._db.collection(_COL).document(estimate_id).get()  # type: ignore[union-attr]
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("tenantId") != tenant_id or data.get("deletedAt") is not None:
            return None
        return _to_entity(data, doc.id)

    def list_by_tenant(
        self,
        tenant_id: str,
        status: str | None = None,
        inspection_id: str | None = None,
    ) -> list[Estimate]:
        q = (
            self._db.collection(_COL)  # type: ignore[union-attr]
            .where("tenantId", "==", tenant_id)
            .where("deletedAt", "==", None)
            .order_by("createdAt", direction="DESCENDING")
        )
        if status:
            q = q.where("status", "==", status)
        if inspection_id:
            q = q.where("inspectionId", "==", inspection_id)
        return [_to_entity(d.to_dict(), d.id) for d in q.stream()]

    def update(
        self,
        estimate_id: str,
        tenant_id: str,
        fields: dict,
        updated_by: str,
    ) -> None:
        mapped: dict = {
            "updatedAt": datetime.now(timezone.utc),
            "updatedBy": updated_by,
        }
        for py_key, fs_key in _UPDATABLE.items():
            if py_key in fields:
                mapped[fs_key] = fields[py_key]
        self._db.collection(_COL).document(estimate_id).update(mapped)  # type: ignore[union-attr]

    def soft_delete(self, estimate_id: str, deleted_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(_COL).document(estimate_id).update({  # type: ignore[union-attr]
            "deletedAt": now,
            "updatedAt": now,
            "updatedBy": deleted_by,
        })
