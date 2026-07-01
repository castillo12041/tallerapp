from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Vehicle:
    id: str
    tenant_id: str
    plate: str  # normalizada: sin guión, mayúsculas (ej: "ABCD12")
    make: str
    model: str
    client_id: str | None
    year: int | None
    color: str | None
    vin: str | None
    engine: str | None
    mileage: int | None
    fuel_type: str | None
    transmission_type: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
