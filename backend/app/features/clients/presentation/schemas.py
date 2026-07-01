from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.clients.domain.entities import Client


class CreateClientRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=60)
    last_name: str = Field(..., min_length=1, max_length=60)
    email: str | None = Field(None, max_length=254)
    phone: str | None = Field(None, max_length=20)
    whatsapp: str | None = Field(None, max_length=20)
    rut: str | None = Field(None, max_length=12)


class UpdateClientRequest(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=60)
    last_name: str | None = Field(None, min_length=1, max_length=60)
    email: str | None = Field(None, max_length=254)
    phone: str | None = Field(None, max_length=20)
    whatsapp: str | None = Field(None, max_length=20)
    rut: str | None = Field(None, max_length=12)


class ClientResponse(BaseModel):
    id: str
    tenant_id: str
    first_name: str
    last_name: str
    full_name: str
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

    @classmethod
    def from_entity(cls, c: Client) -> "ClientResponse":
        return cls(
            id=c.id,
            tenant_id=c.tenant_id,
            first_name=c.first_name,
            last_name=c.last_name,
            full_name=c.full_name,
            email=c.email,
            phone=c.phone,
            whatsapp=c.whatsapp,
            rut=c.rut,
            vehicle_count=c.vehicle_count,
            inspection_count=c.inspection_count,
            total_spent=c.total_spent,
            last_interaction_at=c.last_interaction_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
