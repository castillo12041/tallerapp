from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EstimateItemIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    category: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    inspection_item_id: str | None = None


class CreateEstimateRequest(BaseModel):
    vehicle_id: str
    items: list[EstimateItemIn] = Field(..., min_length=1)
    tax_rate: float = Field(0.19, ge=0, le=1)
    inspection_id: str | None = None
    notes: str | None = Field(None, max_length=2000)
    valid_until: datetime | None = None
    currency: str = Field("CLP", max_length=3)


class UpdateEstimateRequest(BaseModel):
    notes: str | None = Field(None, max_length=2000)
    tax_rate: float | None = Field(None, ge=0, le=1)
    valid_until: datetime | None = None

    def to_fields(self) -> dict:
        out: dict = {}
        if self.notes is not None:
            out["notes"] = self.notes
        if self.tax_rate is not None:
            out["tax_rate"] = self.tax_rate
        if self.valid_until is not None:
            out["valid_until"] = self.valid_until
        return out


class AddItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    category: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    inspection_item_id: str | None = None


class RespondEstimateRequest(BaseModel):
    accepted: bool
    client_notes: str | None = Field(None, max_length=2000)


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


class EstimateItemOut(BaseModel):
    id: str
    estimate_id: str
    name: str
    quantity: float
    unit_price: float
    subtotal: float
    category: str | None
    description: str | None
    inspection_item_id: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str


class EstimateOut(BaseModel):
    id: str
    number: str
    status: str
    tenant_id: str
    inspection_id: str | None
    vehicle_snapshot: VehicleSnapshotOut
    client_snapshot: ClientSnapshotOut | None
    items_count: int
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    currency: str
    notes: str | None
    valid_until: datetime | None
    sent_at: datetime | None
    viewed_at: datetime | None
    responded_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: str


class EstimateWithItemsOut(EstimateOut):
    items: list[EstimateItemOut] = []


class SendEstimateResponse(BaseModel):
    public_url: str
    message: str = "Presupuesto enviado correctamente"


class EstimateListOut(BaseModel):
    items: list[EstimateOut]
    total: int


class PublicEstimateOut(BaseModel):
    """Vista pública del presupuesto — sin datos sensibles del tenant."""

    number: str
    status: str
    vehicle_snapshot: VehicleSnapshotOut
    client_snapshot: ClientSnapshotOut | None
    items: list[EstimateItemOut]
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    currency: str
    notes: str | None
    valid_until: datetime | None
