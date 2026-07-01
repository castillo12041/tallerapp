from __future__ import annotations

from datetime import datetime, timezone

from app.features.inspections.domain.entities import ClientSnapshot, VehicleSnapshot
from app.features.work_orders.domain.entities import WorkOrder

_COL = "work_orders"

_UPDATABLE: dict[str, str] = {
    "status": "status",
    "mechanic_id": "mechanicId",
    "mechanic_name": "mechanicName",
    "diagnosis": "diagnosis",
    "notes": "notes",
    "started_at": "startedAt",
    "waiting_parts_at": "waitingPartsAt",
    "quality_check_at": "qualityCheckAt",
    "completed_at": "completedAt",
    "cancelled_at": "cancelledAt",
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


def _to_entity(data: dict, doc_id: str) -> WorkOrder:
    return WorkOrder(
        id=doc_id,
        tenant_id=data["tenantId"],
        number=data["number"],
        status=data["status"],
        vehicle_snapshot=_snap_v(data),
        client_snapshot=_snap_c(data),
        mechanic_id=data["mechanicId"],
        mechanic_name=data["mechanicName"],
        estimate_id=data.get("estimateId"),
        inspection_id=data.get("inspectionId"),
        diagnosis=data.get("diagnosis"),
        notes=data.get("notes"),
        started_at=data.get("startedAt"),
        waiting_parts_at=data.get("waitingPartsAt"),
        quality_check_at=data.get("qualityCheckAt"),
        completed_at=data.get("completedAt"),
        cancelled_at=data.get("cancelledAt"),
        deleted_at=data.get("deletedAt"),
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
        created_by=data["createdBy"],
        updated_by=data["updatedBy"],
    )


class WorkOrderRepository:
    def __init__(self, db: object) -> None:
        self._db = db

    def create(self, data: dict) -> None:
        self._db.collection(_COL).document(data["id"]).set(data)  # type: ignore[union-attr]

    def find_by_id(self, work_order_id: str, tenant_id: str) -> WorkOrder | None:
        doc = self._db.collection(_COL).document(work_order_id).get()  # type: ignore[union-attr]
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
        mechanic_id: str | None = None,
        estimate_id: str | None = None,
    ) -> list[WorkOrder]:
        q = (
            self._db.collection(_COL)  # type: ignore[union-attr]
            .where("tenantId", "==", tenant_id)
            .where("deletedAt", "==", None)
            .order_by("createdAt", direction="DESCENDING")
        )
        if status:
            q = q.where("status", "==", status)
        if mechanic_id:
            q = q.where("mechanicId", "==", mechanic_id)
        if estimate_id:
            q = q.where("estimateId", "==", estimate_id)
        return [_to_entity(d.to_dict(), d.id) for d in q.stream()]

    def update(
        self,
        work_order_id: str,
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
        self._db.collection(_COL).document(work_order_id).update(mapped)  # type: ignore[union-attr]

    def soft_delete(self, work_order_id: str, deleted_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(_COL).document(work_order_id).update({  # type: ignore[union-attr]
            "deletedAt": now,
            "updatedAt": now,
            "updatedBy": deleted_by,
        })
