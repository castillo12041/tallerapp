from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Tenant:
    id: str
    name: str
    slug: str
    rut: str
    plan_id: str
    subscription_status: str
    is_active: bool
    is_suspended: bool
    storage_used_bytes: int
    inspection_count_this_month: int
    active_user_count: int
    tenant_id: str  # = id; presente por consistencia con el esquema de auditoría
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None
    subscription_id: str | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_operational(self) -> bool:
        return self.is_active and not self.is_suspended and not self.is_deleted
