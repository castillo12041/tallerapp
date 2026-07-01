from __future__ import annotations

from datetime import datetime, timezone

from app.features.inspections.domain.entities import (
    ClientSnapshot,
    Inspection,
    VehicleSnapshot,
)

_COL = "inspections"

_UPDATABLE: dict[str, str] = {
    "general_observations": "generalObservations",
    "recommendations": "recommendations",
    "mileage_at_inspection": "mileageAtInspection",
    "fuel_level": "fuelLevel",
    "client_signature_url": "clientSignatureUrl",
    "report_url": "reportUrl",
    "status": "status",
    "score": "score",
    "good_items": "goodItems",
    "regular_items": "regularItems",
    "bad_items": "badItems",
    "na_items": "naItems",
    "total_repair_cost": "totalRepairCost",
    "started_at": "startedAt",
    "completed_at": "completedAt",
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


def _to_entity(data: dict, doc_id: str) -> Inspection:
    now = datetime.now(timezone.utc)

    def _dt(key: str) -> datetime | None:
        v = data.get(key)
        return v if isinstance(v, datetime) else None

    return Inspection(
        id=doc_id,
        tenant_id=data.get("tenantId", ""),
        number=data.get("number", ""),
        vehicle_id=data.get("vehicleId", ""),
        client_id=data.get("clientId"),
        mechanic_id=data.get("mechanicId", ""),
        template_id=data.get("templateId"),
        status=data.get("status", "draft"),
        vehicle_snapshot=_snap_v(data),
        client_snapshot=_snap_c(data),
        mileage_at_inspection=data.get("mileageAtInspection"),
        fuel_level=data.get("fuelLevel"),
        total_items=data.get("totalItems", 0),
        good_items=data.get("goodItems", 0),
        regular_items=data.get("regularItems", 0),
        bad_items=data.get("badItems", 0),
        na_items=data.get("naItems", 0),
        score=data.get("score"),
        total_repair_cost=data.get("totalRepairCost", 0.0),
        currency=data.get("currency", "CLP"),
        general_observations=data.get("generalObservations"),
        recommendations=data.get("recommendations"),
        client_signature_url=data.get("clientSignatureUrl"),
        report_url=data.get("reportUrl"),
        is_offline=data.get("isOffline", False),
        started_at=_dt("startedAt"),
        completed_at=_dt("completedAt"),
        created_at=_dt("createdAt") or now,
        updated_at=_dt("updatedAt") or now,
        created_by=data.get("createdBy", ""),
        updated_by=data.get("updatedBy", ""),
        deleted_at=_dt("deletedAt"),
    )


class InspectionRepository:
    def __init__(self, db) -> None:
        self._db = db

    def create(self, inspection: Inspection) -> None:
        now = datetime.now(timezone.utc)
        vs = inspection.vehicle_snapshot
        cs = inspection.client_snapshot
        self._db.collection(_COL).document(inspection.id).set({
            "tenantId": inspection.tenant_id,
            "number": inspection.number,
            "vehicleId": inspection.vehicle_id,
            "clientId": inspection.client_id,
            "mechanicId": inspection.mechanic_id,
            "templateId": inspection.template_id,
            "status": inspection.status,
            "vehicleSnapshot": {
                "id": vs.id, "plate": vs.plate, "make": vs.make, "model": vs.model,
                "year": vs.year, "color": vs.color, "vin": vs.vin,
            },
            "clientSnapshot": {
                "id": cs.id, "fullName": cs.full_name, "email": cs.email,
                "phone": cs.phone, "rut": cs.rut,
            } if cs else None,
            "mileageAtInspection": inspection.mileage_at_inspection,
            "fuelLevel": inspection.fuel_level,
            "totalItems": inspection.total_items,
            "goodItems": 0, "regularItems": 0, "badItems": 0, "naItems": 0,
            "score": None, "totalRepairCost": 0.0, "currency": inspection.currency,
            "generalObservations": None, "recommendations": None,
            "clientSignatureUrl": None, "reportUrl": None,
            "isOffline": False, "startedAt": None, "completedAt": None,
            "deletedAt": None, "createdAt": now, "updatedAt": now,
            "createdBy": inspection.created_by, "updatedBy": inspection.updated_by,
        })

    def find_by_id(self, inspection_id: str, tenant_id: str) -> Inspection | None:
        doc = self._db.collection(_COL).document(inspection_id).get()
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
        vehicle_id: str | None = None,
        mechanic_id: str | None = None,
    ) -> list[Inspection]:
        q = self._db.collection(_COL).where("tenantId", "==", tenant_id)
        if status:
            q = q.where("status", "==", status)
        if vehicle_id:
            q = q.where("vehicleId", "==", vehicle_id)
        if mechanic_id:
            q = q.where("mechanicId", "==", mechanic_id)
        results = []
        for doc in q.stream():
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                results.append(_to_entity(data, doc.id))
        return results

    def update(self, inspection_id: str, tenant_id: str, fields: dict, updated_by: str) -> None:
        mapped: dict = {"updatedAt": datetime.now(timezone.utc), "updatedBy": updated_by}
        for py_key, fs_key in _UPDATABLE.items():
            if py_key in fields:
                mapped[fs_key] = fields[py_key]
        self._db.collection(_COL).document(inspection_id).update(mapped)

    def soft_delete(self, inspection_id: str, tenant_id: str, deleted_by: str) -> None:
        self._db.collection(_COL).document(inspection_id).update({
            "deletedAt": datetime.now(timezone.utc),
            "updatedBy": deleted_by,
        })
