from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.rbac import ASSIGNABLE_ROLES
from app.features.users.domain.entities import User

_ASSIGNABLE_PATTERN = "^(" + "|".join(sorted(ASSIGNABLE_ROLES)) + ")$"


class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    display_name: str = Field(..., min_length=2, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=60)
    last_name: str = Field(..., min_length=1, max_length=60)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., pattern=_ASSIGNABLE_PATTERN)
    phone: str | None = Field(None, max_length=20)


class UpdateUserRequest(BaseModel):
    display_name: str | None = Field(None, min_length=2, max_length=100)
    first_name: str | None = Field(None, min_length=1, max_length=60)
    last_name: str | None = Field(None, min_length=1, max_length=60)
    role: str | None = Field(None, pattern=_ASSIGNABLE_PATTERN)
    phone: str | None = Field(None, max_length=20)


class UserResponse(BaseModel):
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

    @classmethod
    def from_entity(cls, u: User) -> "UserResponse":
        return cls(
            uid=u.uid,
            email=u.email,
            display_name=u.display_name,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role,
            permissions=list(u.permissions),
            tenant_id=u.tenant_id,
            plan=u.plan,
            is_active=u.is_active,
            phone=u.phone,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
