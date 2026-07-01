from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.core.firebase import set_custom_claims, verify_firebase_id_token
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.utils import hash_token, run_sync
from app.features.auth.infrastructure.token_repository import RefreshTokenRepository
from app.features.auth.infrastructure.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo

    async def execute(self, firebase_id_token: str) -> TokenResponse:
        # 1. Verificar Firebase ID Token — la SDK es síncrona, corre en executor
        try:
            claims = await run_sync(verify_firebase_id_token, firebase_id_token)
        except Exception:
            raise UnauthorizedException("Firebase ID Token inválido o expirado")

        uid: str = claims["uid"]

        # 2. Cargar usuario desde Firestore
        user = await run_sync(self._user_repo.find_by_uid, uid)
        if user is None:
            raise NotFoundException(
                "Usuario no encontrado. Solicita al administrador que cree tu cuenta."
            )
        if not user.is_active:
            raise ForbiddenException("Cuenta desactivada. Contacta al administrador.")

        # 3. Crear par de tokens
        family_id = str(uuid.uuid4())
        access_token = create_access_token(
            subject=uid,
            tenant_id=user.tenant_id,
            role=user.role,
            permissions=user.permissions,
            plan=user.plan,
        )
        refresh_token = create_refresh_token(
            subject=uid,
            tenant_id=user.tenant_id,
            token_family=family_id,
        )

        # 4. Persistir hash del refresh token (nunca el token en claro)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await run_sync(
            self._token_repo.create,
            family_id,
            hash_token(refresh_token),
            uid,
            user.tenant_id,
            expires_at,
        )

        # 5. Sincronizar custom claims en Firebase Auth para las próximas requests
        await run_sync(
            set_custom_claims,
            uid,
            {
                "tenantId": user.tenant_id,
                "role": user.role,
                "permissions": user.permissions,
                "plan": user.plan,
            },
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class RefreshUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo

    async def execute(self, raw_refresh_token: str) -> TokenResponse:
        # 1. Decodificar y verificar estructura del token (firma + expiración)
        payload = decode_refresh_token(raw_refresh_token)
        uid: str = payload["sub"]
        family_id: str = payload["token_family"]

        # 2. Verificar el hash contra lo almacenado en Firestore
        record = await run_sync(self._token_repo.find_by_family, family_id)
        if record is None or not record.is_valid():
            raise UnauthorizedException("Refresh token inválido o expirado.")

        if not record.matches(hash_token(raw_refresh_token)):
            # Reuso detectado: token ya rotado presentado de nuevo → posible robo
            await run_sync(self._token_repo.revoke_family, family_id, uid)
            raise UnauthorizedException(
                "Sesión comprometida. Inicia sesión nuevamente."
            )

        # 3. Verificar que el usuario sigue activo
        user = await run_sync(self._user_repo.find_by_uid, uid)
        if user is None or not user.is_active:
            await run_sync(self._token_repo.revoke_family, family_id, uid)
            raise ForbiddenException("Cuenta no disponible.")

        # 4. Generar nuevo par — misma familia, hash nuevo
        new_access = create_access_token(
            subject=uid,
            tenant_id=user.tenant_id,
            role=user.role,
            permissions=user.permissions,
            plan=user.plan,
        )
        new_refresh = create_refresh_token(
            subject=uid,
            tenant_id=user.tenant_id,
            token_family=family_id,
        )

        new_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await run_sync(
            self._token_repo.rotate,
            family_id,
            hash_token(new_refresh),
            new_expires_at,
            uid,
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class LogoutUseCase:
    def __init__(self, token_repo: RefreshTokenRepository) -> None:
        self._token_repo = token_repo

    async def execute(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_refresh_token(raw_refresh_token)
            family_id: str = payload["token_family"]
            uid: str = payload["sub"]
            await run_sync(self._token_repo.revoke_family, family_id, uid)
        except UnauthorizedException:
            # Token expirado o inválido — el logout es efectivo igual.
            pass
