from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.features.vehicles.domain.entities import Vehicle

_FIELD_MAP: dict[str, str] = {
    "plate": "plate",
    "make": "make",
    "model": "model",
    "client_id": "clientId",
    "year": "year",
    "color": "color",
    "vin": "vin",
    "engine": "engine",
    "mileage": "mileage",
    "fuel_type": "fuelType",
    "transmission_type": "transmissionType",
}


class VehicleRepository:
    _COLLECTION = "vehicles"

    def __init__(self, db: firestore.Client) -> None:
        self._db = db

    def create(self, vehicle: Vehicle) -> None:
        self._db.collection(self._COLLECTION).document(vehicle.id).set(
            self._to_firestore(vehicle)
        )

    def find_by_id(self, vehicle_id: str, tenant_id: str) -> Vehicle | None:
        doc = self._db.collection(self._COLLECTION).document(vehicle_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("deletedAt") is not None:
            return None
        if data.get("tenantId") != tenant_id:
            return None
        return self._to_entity(doc.id, data)

    def find_by_plate(self, plate: str, tenant_id: str) -> Vehicle | None:
        docs = (
            self._db.collection(self._COLLECTION)
            .where("tenantId", "==", tenant_id)
            .where("plate", "==", plate)
            .limit(1)
            .stream()
        )
        for doc in docs:
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                return self._to_entity(doc.id, data)
        return None

    def list_by_tenant(
        self,
        tenant_id: str,
        client_id: str | None = None,
        search: str | None = None,
    ) -> list[Vehicle]:
        query = self._db.collection(self._COLLECTION).where("tenantId", "==", tenant_id)
        if client_id:
            query = query.where("clientId", "==", client_id)
        docs = query.stream()
        vehicles = [
            self._to_entity(doc.id, doc.to_dict())
            for doc in docs
            if doc.to_dict().get("deletedAt") is None
        ]
        if search:
            term = search.lower()
            vehicles = [
                v for v in vehicles
                if term in v.plate.lower()
                or term in v.make.lower()
                or term in v.model.lower()
                or (v.vin and term in v.vin.lower())
            ]
        return vehicles

    def update(self, vehicle_id: str, tenant_id: str, fields: dict, updated_by: str) -> None:
        firestore_data: dict = {
            _FIELD_MAP[k]: v
            for k, v in fields.items()
            if k in _FIELD_MAP
        }
        firestore_data["updatedAt"] = datetime.now(timezone.utc)
        firestore_data["updatedBy"] = updated_by
        self._db.collection(self._COLLECTION).document(vehicle_id).update(firestore_data)

    def soft_delete(self, vehicle_id: str, tenant_id: str, deleted_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(self._COLLECTION).document(vehicle_id).update({
            "deletedAt": now,
            "updatedAt": now,
            "updatedBy": deleted_by,
        })

    # ------------------------------------------------------------------

    def _to_firestore(self, v: Vehicle) -> dict:
        return {
            "tenantId": v.tenant_id,
            "plate": v.plate,
            "make": v.make,
            "model": v.model,
            "clientId": v.client_id,
            "year": v.year,
            "color": v.color,
            "vin": v.vin,
            "engine": v.engine,
            "mileage": v.mileage,
            "fuelType": v.fuel_type,
            "transmissionType": v.transmission_type,
            "createdAt": v.created_at,
            "updatedAt": v.updated_at,
            "createdBy": v.created_by,
            "updatedBy": v.updated_by,
            "deletedAt": v.deleted_at,
        }

    def _to_entity(self, doc_id: str, data: dict) -> Vehicle:
        def _dt(val: object) -> datetime:
            if isinstance(val, datetime):
                return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
            raise ValueError(f"Expected datetime, got {type(val)}")

        def _dt_opt(val: object) -> datetime | None:
            return None if val is None else _dt(val)

        return Vehicle(
            id=doc_id,
            tenant_id=data["tenantId"],
            plate=data.get("plate", ""),
            make=data.get("make", ""),
            model=data.get("model", ""),
            client_id=data.get("clientId"),
            year=data.get("year"),
            color=data.get("color"),
            vin=data.get("vin"),
            engine=data.get("engine"),
            mileage=data.get("mileage"),
            fuel_type=data.get("fuelType"),
            transmission_type=data.get("transmissionType"),
            created_at=_dt(data["createdAt"]),
            updated_at=_dt(data["updatedAt"]),
            created_by=data.get("createdBy", ""),
            updated_by=data.get("updatedBy", ""),
            deleted_at=_dt_opt(data.get("deletedAt")),
        )
