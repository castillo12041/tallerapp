from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.features.inspections.domain.entities import ClientSnapshot, VehicleSnapshot


@dataclass(frozen=True)
class WorkOrderEntry:
    """Bitácora de cambios y notas sobre una OT."""

    id: str
    tenant_id: str
    work_order_id: str
    entry_type: str          # "status_change" | "note" | "parts_update"
    created_at: datetime
    created_by: str
    from_status: str | None = None
    to_status: str | None = None
    content: str | None = None   # texto libre para notas


@dataclass(frozen=True)
class WorkOrder:
    id: str
    tenant_id: str
    number: str              # OT-{año}-{NNNNNN}
    status: str              # pending|in_progress|waiting_parts|quality_check|completed|cancelled
    vehicle_snapshot: VehicleSnapshot
    mechanic_id: str
    mechanic_name: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    estimate_id: str | None = None
    inspection_id: str | None = None
    client_snapshot: ClientSnapshot | None = None
    diagnosis: str | None = None
    notes: str | None = None
    started_at: datetime | None = None
    waiting_parts_at: datetime | None = None
    quality_check_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_terminal(self) -> bool:
        return self.status in {"completed", "cancelled"}
