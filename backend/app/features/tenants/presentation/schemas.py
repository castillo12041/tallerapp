from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.tenants.domain.entities import Tenant


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    rut: str = Field(..., min_length=8, max_length=12)
    plan_id: str = Field(default="basic", pattern=r"^(basic|professional|premium|enterprise)$")


class UpdateTenantRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    plan_id: str | None = Field(None, pattern=r"^(basic|professional|premium|enterprise)$")
    is_active: bool | None = None
    is_suspended: bool | None = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    rut: str
    plan_id: str
    subscription_status: str
    is_active: bool
    is_suspended: bool
    active_user_count: int
    inspection_count_this_month: int
    storage_used_bytes: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, t: Tenant) -> "TenantResponse":
        return cls(
            id=t.id,
            name=t.name,
            slug=t.slug,
            rut=t.rut,
            plan_id=t.plan_id,
            subscription_status=t.subscription_status,
            is_active=t.is_active,
            is_suspended=t.is_suspended,
            active_user_count=t.active_user_count,
            inspection_count_this_month=t.inspection_count_this_month,
            storage_used_bytes=t.storage_used_bytes,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )


class SubscriptionResponse(BaseModel):
    tenant_id: str
    plan_id: str
    subscription_status: str
    subscription_id: str | None
    storage_used_bytes: int
    inspection_count_this_month: int
    active_user_count: int

    @classmethod
    def from_entity(cls, t: Tenant) -> "SubscriptionResponse":
        return cls(
            tenant_id=t.id,
            plan_id=t.plan_id,
            subscription_status=t.subscription_status,
            subscription_id=t.subscription_id,
            storage_used_bytes=t.storage_used_bytes,
            inspection_count_this_month=t.inspection_count_this_month,
            active_user_count=t.active_user_count,
        )
