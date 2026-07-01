from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import Request

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.schemas.auth import TokenPayload

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenPayload:
    """
    Extrae y valida el JWT de la cabecera Authorization.
    Escribe user_id y tenant_id en request.state para que AuditMiddleware los use.
    """
    if not credentials:
        raise UnauthorizedException("Cabecera Authorization requerida")

    payload = decode_access_token(credentials.credentials)

    try:
        user = TokenPayload(**payload)
    except Exception:
        raise UnauthorizedException("Payload del token inválido")

    request.state.user_id = user.sub
    request.state.tenant_id = user.tenant_id
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenPayload | None:
    """Igual que get_current_user pero retorna None en lugar de lanzar excepción."""
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user = TokenPayload(**payload)
        request.state.user_id = user.sub
        request.state.tenant_id = user.tenant_id
        return user
    except Exception:
        return None


CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
OptionalUser = Annotated[TokenPayload | None, Depends(get_current_user_optional)]
