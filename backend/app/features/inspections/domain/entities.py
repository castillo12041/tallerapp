from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VehicleSnapshot:
    id: str
    plate: str
    make: str
    model: str
    year: int | None = None
    color: str | None = None
    vin: str | None = None


@dataclass(frozen=True)
class ClientSnapshot:
    id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    rut: str | None = None


@dataclass(frozen=True)
class InspectionItem:
    id: str
    tenant_id: str
    inspection_id: str
    category: str
    category_order: int
    name: str
    order: int
    status: str  # pending|good|regular|bad|na
    photo_urls: tuple[str, ...]
    photo_count: int
    is_offline: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    observation: str | None = None
    repair_cost: float | None = None
    audio_url: str | None = None


@dataclass(frozen=True)
class Inspection:
    id: str
    tenant_id: str
    number: str          # INS-2024-001234
    vehicle_id: str
    mechanic_id: str
    status: str          # draft|in_progress|review|completed|cancelled
    vehicle_snapshot: VehicleSnapshot
    total_items: int
    good_items: int
    regular_items: int
    bad_items: int
    na_items: int
    total_repair_cost: float
    currency: str
    is_offline: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    client_id: str | None = None
    template_id: str | None = None
    client_snapshot: ClientSnapshot | None = None
    mileage_at_inspection: int | None = None
    fuel_level: str | None = None
    score: float | None = None
    general_observations: str | None = None
    recommendations: str | None = None
    client_signature_url: str | None = None
    report_url: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
