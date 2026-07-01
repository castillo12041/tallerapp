from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Client:
    id: str
    tenant_id: str
    first_name: str
    last_name: str
    full_name: str  # desnormalizado: "{first_name} {last_name}"
    email: str | None
    phone: str | None
    whatsapp: str | None
    rut: str | None
    vehicle_count: int
    inspection_count: int
    total_spent: float
    last_interaction_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
