from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.features.inspections.domain.entities import ClientSnapshot, VehicleSnapshot


@dataclass(frozen=True)
class EstimateItem:
    id: str
    tenant_id: str
    estimate_id: str
    name: str
    quantity: float
    unit_price: float
    subtotal: float           # = quantity * unit_price (calculado al persistir)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    category: str | None = None
    description: str | None = None
    inspection_item_id: str | None = None  # referencia al ítem de inspección origen


@dataclass(frozen=True)
class Estimate:
    id: str
    tenant_id: str
    number: str               # EST-2024-000001
    status: str               # draft|sent|viewed|accepted|rejected|converted
    vehicle_snapshot: VehicleSnapshot
    items_count: int
    subtotal: float
    tax_rate: float           # ej. 0.19
    tax_amount: float         # subtotal * tax_rate
    total: float              # subtotal + tax_amount
    currency: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    inspection_id: str | None = None
    client_snapshot: ClientSnapshot | None = None
    notes: str | None = None           # nota interna del taller
    client_notes: str | None = None    # comentario del cliente al aceptar/rechazar
    public_token_id: str | None = None # jti del token público (set al enviar)
    valid_until: datetime | None = None
    sent_at: datetime | None = None
    viewed_at: datetime | None = None
    responded_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
