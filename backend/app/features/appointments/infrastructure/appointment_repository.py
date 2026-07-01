from __future__ import annotations

from datetime import datetime, timezone

from app.features.appointments.domain.entities import Appointment

_COL = "appointments"

_UPDATABLE: dict[str, str] = {
    "type": "type",
    "status": "status",
    "title": "title",
    "start_at": "startAt",
    "end_at": "endAt",
    "all_day": "allDay",
    "client_id": "clientId",
    "vehicle_id": "vehicleId",
    "mechanic_id": "mechanicId",
    "mechanic_name": "mechanicName",
    "inspection_id": "inspectionId",
    "work_order_id": "workOrderId",
    "notes": "notes",
    "reminder_minutes": "reminderMinutes",
    "cancel_reason": "cancelReason",
    "cancelled_at": "cancelledAt",
}


def _to_entity(data: dict, doc_id: str) -> Appointment:
    return Appointment(
        id=doc_id,
        tenant_id=data["tenantId"],
        type=data["type"],
        status=data["status"],
        title=data["title"],
        start_at=data["startAt"],
        end_at=data["endAt"],
        all_day=data.get("allDay", False),
        client_id=data.get("clientId"),
        vehicle_id=data.get("vehicleId"),
        mechanic_id=data.get("mechanicId"),
        mechanic_name=data.get("mechanicName"),
        inspection_id=data.get("inspectionId"),
        work_order_id=data.get("workOrderId"),
        notes=data.get("notes"),
        reminder_minutes=data.get("reminderMinutes"),
        cancel_reason=data.get("cancelReason"),
        cancelled_at=data.get("cancelledAt"),
        deleted_at=data.get("deletedAt"),
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
        created_by=data["createdBy"],
        updated_by=data["updatedBy"],
    )


class AppointmentRepository:
    def __init__(self, db: object) -> None:
        self._db = db

    def create(self, data: dict) -> None:
        self._db.collection(_COL).document(data["id"]).set(data)  # type: ignore[union-attr]

    def find_by_id(self, appointment_id: str, tenant_id: str) -> Appointment | None:
        doc = self._db.collection(_COL).document(appointment_id).get()  # type: ignore[union-attr]
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("tenantId") != tenant_id or data.get("deletedAt") is not None:
            return None
        return _to_entity(data, doc.id)

    def list_by_tenant(
        self,
        tenant_id: str,
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        mechanic_id: str | None = None,
        status: str | None = None,
        appointment_type: str | None = None,
    ) -> list[Appointment]:
        q = (
            self._db.collection(_COL)  # type: ignore[union-attr]
            .where("tenantId", "==", tenant_id)
            .where("deletedAt", "==", None)
        )
        if date_start:
            q = q.where("startAt", ">=", date_start)
        if date_end:
            q = q.where("startAt", "<", date_end)
        if mechanic_id:
            q = q.where("mechanicId", "==", mechanic_id)
        if status:
            q = q.where("status", "==", status)
        if appointment_type:
            q = q.where("type", "==", appointment_type)
        q = q.order_by("startAt")
        return [_to_entity(d.to_dict(), d.id) for d in q.stream()]

    def find_conflicts(
        self,
        tenant_id: str,
        mechanic_id: str,
        start_at: datetime,
        end_at: datetime,
        exclude_id: str | None = None,
    ) -> list[Appointment]:
        """Returns appointments overlapping [start_at, end_at) for the mechanic."""
        q = (
            self._db.collection(_COL)  # type: ignore[union-attr]
            .where("tenantId", "==", tenant_id)
            .where("mechanicId", "==", mechanic_id)
            .where("deletedAt", "==", None)
            .where("startAt", "<", end_at)
            .order_by("startAt")
        )
        results = []
        for d in q.stream():
            if exclude_id and d.id == exclude_id:
                continue
            data = d.to_dict()
            if data.get("status") in {"cancelled", "no_show"}:
                continue
            appt_end = data.get("endAt")
            if appt_end and appt_end > start_at:
                results.append(_to_entity(data, d.id))
        return results

    def update(
        self,
        appointment_id: str,
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
        self._db.collection(_COL).document(appointment_id).update(mapped)  # type: ignore[union-attr]

    def soft_delete(self, appointment_id: str, deleted_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(_COL).document(appointment_id).update({  # type: ignore[union-attr]
            "deletedAt": now,
            "updatedAt": now,
            "updatedBy": deleted_by,
        })
