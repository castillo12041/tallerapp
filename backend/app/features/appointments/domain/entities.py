from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Appointment:
    id: str
    tenant_id: str
    type: str          # inspection | work_order | appointment | reminder
    status: str        # scheduled | confirmed | in_progress | completed | cancelled | no_show
    title: str
    start_at: datetime
    end_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    all_day: bool = False
    client_id: str | None = None
    vehicle_id: str | None = None
    mechanic_id: str | None = None
    mechanic_name: str | None = None
    inspection_id: str | None = None
    work_order_id: str | None = None
    notes: str | None = None
    reminder_minutes: int | None = None
    cancel_reason: str | None = None
    cancelled_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_terminal(self) -> bool:
        return self.status in {"completed", "cancelled", "no_show"}

    @property
    def duration_minutes(self) -> int:
        delta = self.end_at - self.start_at
        return int(delta.total_seconds() / 60)
