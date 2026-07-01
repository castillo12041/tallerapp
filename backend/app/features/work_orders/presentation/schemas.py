from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateWorkOrderRequest(BaseModel):
    mechanic_id: str
    estimate_id: str | None = None
    inspection_id: str | None = None
    notes: str | None = Field(None, max_length=2000)
    diagnosis: str | None = Field(None, max_length=2000)


class UpdateWorkOrderRequest(BaseModel):
    mechanic_id: str | None = None
    notes: str | None = Field(None, max_length=2000)
    diagnosis: str | None = Field(None, max_length=2000)

    def to_fields(self) -> dict:
        out: dict = {}
        if self.mechanic_id is not None:
            out["mechanic_id"] = self.mechanic_id
        if self.notes is not None:
            out["notes"] = self.notes
        if self.diagnosis is not None:
            out["diagnosis"] = self.diagnosis
        return out


class WaitPartsRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class CancelWorkOrderRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class AddEntryRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


# ── Response schemas ──────────────────────────────────────────────────────────


class VehicleSnapshotOut(BaseModel):
    id: str
    plate: str
    make: str
    model: str
    year: int | None
    color: str | None
    vin: str | None


class ClientSnapshotOut(BaseModel):
    id: str
    full_name: str
    email: str | None
    phone: str | None
    rut: str | None


class WorkOrderEntryOut(BaseModel):
    id: str
    work_order_id: str
    entry_type: str
    from_status: str | None
    to_status: str | None
    content: str | None
    created_at: datetime
    created_by: str


class WorkOrderOut(BaseModel):
    id: str
    number: str
    status: str
    tenant_id: str
    estimate_id: str | None
    inspection_id: str | None
    vehicle_snapshot: VehicleSnapshotOut
    client_snapshot: ClientSnapshotOut | None
    mechanic_id: str
    mechanic_name: str
    diagnosis: str | None
    notes: str | None
    started_at: datetime | None
    waiting_parts_at: datetime | None
    quality_check_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: str


class WorkOrderWithEntriesOut(WorkOrderOut):
    entries: list[WorkOrderEntryOut] = []


class WorkOrderListOut(BaseModel):
    items: list[WorkOrderOut]
    total: int
