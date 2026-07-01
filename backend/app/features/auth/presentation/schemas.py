from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    id_token: str = Field(
        description=(
            "Firebase ID Token obtenido por el cliente tras autenticarse con Firebase. "
            "Se verifica en el backend con el Admin SDK."
        )
    )


class LogoutRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token a invalidar.")
