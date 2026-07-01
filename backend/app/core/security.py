"""
Operaciones JWT para la API de Taller Inspección.

Usa PyJWT con HS256. El JWT interno se genera DESPUÉS de verificar
el Firebase ID Token en el endpoint de login. No reemplaza Firebase Auth;
complementa el flujo añadiendo claims de tenant, rol y permisos.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.core.exceptions import UnauthorizedException


def create_access_token(
    subject: str,
    tenant_id: str | None,
    role: str,
    permissions: list[str],
    plan: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "permissions": permissions,
        "plan": plan,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    tenant_id: str | None,
    token_family: str,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "token_family": token_family,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza UnauthorizedException si es inválido."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise UnauthorizedException("Token expirado")
    except (DecodeError, InvalidTokenError):
        raise UnauthorizedException("Token inválido")


def decode_access_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise UnauthorizedException("Tipo de token incorrecto")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Tipo de token incorrecto")
    return payload
