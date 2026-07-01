from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.firebase import get_firestore
from app.dependencies.auth import CurrentUser
from app.features.auth.application.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    RefreshUseCase,
)
from app.features.auth.infrastructure.token_repository import RefreshTokenRepository
from app.features.auth.infrastructure.user_repository import UserRepository
from app.features.auth.presentation.schemas import LoginRequest, LogoutRequest
from app.schemas.auth import RefreshRequest, TokenPayload, TokenResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories — permiten override en tests
# ---------------------------------------------------------------------------


def _get_user_repo() -> UserRepository:
    return UserRepository(get_firestore())


def _get_token_repo() -> RefreshTokenRepository:
    return RefreshTokenRepository(get_firestore())


def _get_login_use_case(
    user_repo: UserRepository = Depends(_get_user_repo),
    token_repo: RefreshTokenRepository = Depends(_get_token_repo),
) -> LoginUseCase:
    return LoginUseCase(user_repo=user_repo, token_repo=token_repo)


def _get_refresh_use_case(
    user_repo: UserRepository = Depends(_get_user_repo),
    token_repo: RefreshTokenRepository = Depends(_get_token_repo),
) -> RefreshUseCase:
    return RefreshUseCase(user_repo=user_repo, token_repo=token_repo)


def _get_logout_use_case(
    token_repo: RefreshTokenRepository = Depends(_get_token_repo),
) -> LogoutUseCase:
    return LogoutUseCase(token_repo=token_repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description=(
        "Verifica el Firebase ID Token del cliente y retorna un par de tokens "
        "internos (access + refresh) con claims de tenant, rol y permisos."
    ),
)
async def login(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(_get_login_use_case),
) -> TokenResponse:
    return await use_case.execute(body.id_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens",
    description=(
        "Rota el refresh token. El token anterior queda invalidado. "
        "Si se detecta reuso del token (posible robo), se revoca la sesión completa."
    ),
)
async def refresh(
    body: RefreshRequest,
    use_case: RefreshUseCase = Depends(_get_refresh_use_case),
) -> TokenResponse:
    return await use_case.execute(body.refresh_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Cerrar sesión",
    description="Invalida la familia de refresh tokens del usuario. No requiere estar autenticado.",
)
async def logout(
    body: LogoutRequest,
    use_case: LogoutUseCase = Depends(_get_logout_use_case),
) -> None:
    await use_case.execute(body.refresh_token)


@router.get(
    "/me",
    response_model=TokenPayload,
    summary="Perfil del usuario autenticado",
    description="Retorna los claims del JWT del usuario actualmente autenticado.",
)
async def me(current_user: CurrentUser) -> TokenPayload:
    return current_user
