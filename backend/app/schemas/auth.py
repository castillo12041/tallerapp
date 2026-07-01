from __future__ import annotations

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """Claims del JWT interno. Generado por el backend tras verificar el Firebase ID Token."""

    sub: str = Field(description="Firebase UID del usuario")
    tenant_id: str | None = Field(default=None, description="ID del tenant (None para superadmin)")
    role: str = Field(description="Rol del usuario en el sistema")
    permissions: list[str] = Field(default_factory=list, description="Permisos explícitos del usuario")
    plan: str | None = Field(default=None, description="Plan del tenant (basic, professional, premium, enterprise)")
    type: str = Field(default="access")
    exp: int
    iat: int

    @property
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"

    @property
    def has_tenant(self) -> bool:
        return self.tenant_id is not None

    def has_permission(self, permission: str) -> bool:
        if self.is_superadmin:
            return True
        return permission in self.permissions


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="Segundos hasta expiración del access token")


class RefreshRequest(BaseModel):
    refresh_token: str
