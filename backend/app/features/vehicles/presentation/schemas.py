from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.vehicles.domain.entities import Vehicle

_FUEL_TYPES = r"^(gasoline|diesel|electric|hybrid|lpg|other)$"
_TRANS_TYPES = r"^(manual|automatic|cvt|other)$"


class CreateVehicleRequest(BaseModel):
    plate: str = Field(..., min_length=4, max_length=10)
    make: str = Field(..., min_length=1, max_length=60)
    model: str = Field(..., min_length=1, max_length=60)
    client_id: str | None = None
    year: int | None = Field(None, ge=1900, le=2100)
    color: str | None = Field(None, max_length=30)
    vin: str | None = Field(None, max_length=17)
    engine: str | None = Field(None, max_length=50)
    mileage: int | None = Field(None, ge=0)
    fuel_type: str | None = Field(None, pattern=_FUEL_TYPES)
    transmission_type: str | None = Field(None, pattern=_TRANS_TYPES)


class UpdateVehicleRequest(BaseModel):
    plate: str | None = Field(None, min_length=4, max_length=10)
    make: str | None = Field(None, min_length=1, max_length=60)
    model: str | None = Field(None, min_length=1, max_length=60)
    client_id: str | None = None
    year: int | None = Field(None, ge=1900, le=2100)
    color: str | None = Field(None, max_length=30)
    vin: str | None = Field(None, max_length=17)
    engine: str | None = Field(None, max_length=50)
    mileage: int | None = Field(None, ge=0)
    fuel_type: str | None = Field(None, pattern=_FUEL_TYPES)
    transmission_type: str | None = Field(None, pattern=_TRANS_TYPES)


class VehicleResponse(BaseModel):
    id: str
    tenant_id: str
    plate: str
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

    @classmethod
    def from_entity(cls, v: Vehicle) -> "VehicleResponse":
        return cls(
            id=v.id,
            tenant_id=v.tenant_id,
            plate=v.plate,
            make=v.make,
            model=v.model,
            client_id=v.client_id,
            year=v.year,
            color=v.color,
            vin=v.vin,
            engine=v.engine,
            mileage=v.mileage,
            fuel_type=v.fuel_type,
            transmission_type=v.transmission_type,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
