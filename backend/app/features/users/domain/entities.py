from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    uid: str
    email: str
    display_name: str
    first_name: str
    last_name: str
    role: str
    permissions: list[str]
    tenant_id: str
    plan: str | None
    is_active: bool
    phone: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
