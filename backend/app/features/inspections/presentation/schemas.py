from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.inspections.domain.entities import (
    ClientSnapshot,
    Inspection,
    InspectionItem,
    VehicleSnapshot,
)
from app.features.inspections.domain.workflow import ALL_STATUSES

_FUEL_LEVELS = r"^(empty|quarter|half|three_quarters|full)$"


class CreateInspectionRequest(BaseModel):
    vehicle_id: str
    mechanic_id: str
    client_id: str | None = None
    template_id: str | None = None
    mileage_at_inspection: int | None = Field(None, ge=0)
    fuel_level: str | None = Field(None, pattern=_FUEL_LEVELS)


class UpdateInspectionRequest(BaseModel):
    general_observations: str | None = Field(None, max_length=2000)
    recommendations: str | None = Field(None, max_length=2000)
    mileage_at_inspection: int | None = Field(None, ge=0)
    fuel_level: str | None = Field(None, pattern=_FUEL_LEVELS)


class UpdateItemRequest(BaseModel):
    status: str | None = Field(None, pattern=r"^(pending|good|regular|bad|na)$")
    observation: str | None = Field(None, max_length=1000)
    repair_cost: float | None = Field(None, ge=0)
    photo_urls: list[str] | None = None
    audio_url: str | None = None


# --- Responses ---

class VehicleSnapshotResponse(BaseModel):
    id: str
    plate: str
    make: str
    model: str
    year: int | None
    color: str | None

    @classmethod
    def from_entity(cls, s: VehicleSnapshot) -> "VehicleSnapshotResponse":
        return cls(id=s.id, plate=s.plate, make=s.make, model=s.model, year=s.year, color=s.color)


class ClientSnapshotResponse(BaseModel):
    id: str
    full_name: str
    email: str | None
    phone: str | None

    @classmethod
    def from_entity(cls, s: ClientSnapshot) -> "ClientSnapshotResponse":
        return cls(id=s.id, full_name=s.full_name, email=s.email, phone=s.phone)


class InspectionItemResponse(BaseModel):
    id: str
    category: str
    category_order: int
    name: str
    order: int
    status: str
    observation: str | None
    repair_cost: float | None
    photo_urls: list[str]
    photo_count: int
    audio_url: str | None

    @classmethod
    def from_entity(cls, it: InspectionItem) -> "InspectionItemResponse":
        return cls(
            id=it.id, category=it.category, category_order=it.category_order,
            name=it.name, order=it.order, status=it.status,
            observation=it.observation, repair_cost=it.repair_cost,
            photo_urls=list(it.photo_urls), photo_count=it.photo_count,
            audio_url=it.audio_url,
        )


class InspectionResponse(BaseModel):
    id: str
    tenant_id: str
    number: str
    vehicle_id: str
    client_id: str | None
    mechanic_id: str
    template_id: str | None
    status: str
    vehicle_snapshot: VehicleSnapshotResponse
    client_snapshot: ClientSnapshotResponse | None
    mileage_at_inspection: int | None
    fuel_level: str | None
    total_items: int
    good_items: int
    regular_items: int
    bad_items: int
    na_items: int
    score: float | None
    total_repair_cost: float
    currency: str
    general_observations: str | None
    recommendations: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[InspectionItemResponse] | None = None

    @classmethod
    def from_entity(
        cls,
        inspection: Inspection,
        items: list[InspectionItem] | None = None,
    ) -> "InspectionResponse":
        return cls(
            id=inspection.id,
            tenant_id=inspection.tenant_id,
            number=inspection.number,
            vehicle_id=inspection.vehicle_id,
            client_id=inspection.client_id,
            mechanic_id=inspection.mechanic_id,
            template_id=inspection.template_id,
            status=inspection.status,
            vehicle_snapshot=VehicleSnapshotResponse.from_entity(inspection.vehicle_snapshot),
            client_snapshot=(
                ClientSnapshotResponse.from_entity(inspection.client_snapshot)
                if inspection.client_snapshot else None
            ),
            mileage_at_inspection=inspection.mileage_at_inspection,
            fuel_level=inspection.fuel_level,
            total_items=inspection.total_items,
            good_items=inspection.good_items,
            regular_items=inspection.regular_items,
            bad_items=inspection.bad_items,
            na_items=inspection.na_items,
            score=inspection.score,
            total_repair_cost=inspection.total_repair_cost,
            currency=inspection.currency,
            general_observations=inspection.general_observations,
            recommendations=inspection.recommendations,
            started_at=inspection.started_at,
            completed_at=inspection.completed_at,
            created_at=inspection.created_at,
            updated_at=inspection.updated_at,
            items=[InspectionItemResponse.from_entity(it) for it in items] if items is not None else None,
        )
