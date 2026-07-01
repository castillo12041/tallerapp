from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class CreateAppointmentRequest(BaseModel):
    type: str = Field(..., pattern="^(inspection|work_order|appointment|reminder)$")
    title: str = Field(..., min_length=1, max_length=200)
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    client_id: str | None = None
    vehicle_id: str | None = None
    mechanic_id: str | None = None
    mechanic_name: str | None = None
    inspection_id: str | None = None
    work_order_id: str | None = None
    notes: str | None = Field(None, max_length=1000)
    reminder_minutes: int | None = Field(None, ge=0, le=10080)  # max 1 semana

    @model_validator(mode="after")
    def end_after_start(self) -> CreateAppointmentRequest:
        if not self.all_day and self.end_at <= self.start_at:
            raise ValueError("end_at debe ser posterior a start_at")
        return self


class UpdateAppointmentRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    mechanic_id: str | None = None
    mechanic_name: str | None = None
    notes: str | None = Field(None, max_length=1000)
    reminder_minutes: int | None = Field(None, ge=0, le=10080)
    status: str | None = Field(
        None,
        pattern="^(scheduled|confirmed|in_progress|completed|cancelled|no_show)$",
    )

    def to_fields(self) -> dict:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class CancelAppointmentRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class AppointmentOut(BaseModel):
    id: str
    tenant_id: str
    type: str
    status: str
    title: str
    start_at: datetime
    end_at: datetime
    all_day: bool
    client_id: str | None
    vehicle_id: str | None
    mechanic_id: str | None
    mechanic_name: str | None
    inspection_id: str | None
    work_order_id: str | None
    notes: str | None
    reminder_minutes: int | None
    cancel_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: str

    model_config = {"from_attributes": True}


class AppointmentListOut(BaseModel):
    items: list[AppointmentOut]
    total: int


class AvailabilitySlotOut(BaseModel):
    start_at: datetime
    end_at: datetime
    available: bool


class AvailabilityOut(BaseModel):
    date: str
    mechanic_id: str | None
    duration_minutes: int
    slots: list[AvailabilitySlotOut]
