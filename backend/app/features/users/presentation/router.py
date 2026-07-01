from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.exceptions import ForbiddenException
from app.core.firebase import get_firestore
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import require_permission, require_tenant
from app.features.users.application.use_cases import (
    CreateUserUseCase,
    DeactivateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from app.features.users.infrastructure.user_crud_repository import UserCrudRepository
from app.features.users.presentation.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories — exportadas para override en tests
# ---------------------------------------------------------------------------


def _get_repo() -> UserCrudRepository:
    return UserCrudRepository(db=get_firestore())


def _get_create_uc(repo: Annotated[UserCrudRepository, Depends(_get_repo)]) -> CreateUserUseCase:
    return CreateUserUseCase(repo)


def _get_get_uc(repo: Annotated[UserCrudRepository, Depends(_get_repo)]) -> GetUserUseCase:
    return GetUserUseCase(repo)


def _get_list_uc(repo: Annotated[UserCrudRepository, Depends(_get_repo)]) -> ListUsersUseCase:
    return ListUsersUseCase(repo)


def _get_update_uc(repo: Annotated[UserCrudRepository, Depends(_get_repo)]) -> UpdateUserUseCase:
    return UpdateUserUseCase(repo)


def _get_deactivate_uc(
    repo: Annotated[UserCrudRepository, Depends(_get_repo)],
) -> DeactivateUserUseCase:
    return DeactivateUserUseCase(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="Crear usuario",
    description="Requiere permiso 'users:create'. Crea el usuario en Firebase Auth y Firestore.",
)
async def create_user(
    body: CreateUserRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("users:create"))],
    use_case: Annotated[CreateUserUseCase, Depends(_get_create_uc)],
) -> UserResponse:
    tenant_id = _resolve_tenant_id(current_user)
    user = await use_case.execute(
        email=body.email,
        display_name=body.display_name,
        first_name=body.first_name,
        last_name=body.last_name,
        password=body.password,
        role=body.role,
        tenant_id=tenant_id,
        plan=current_user.plan,
        phone=body.phone,
        created_by=current_user.sub,
    )
    return UserResponse.from_entity(user)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    description="Requiere permiso 'users:read'. Devuelve usuarios del tenant del solicitante.",
)
async def list_users(
    current_user: Annotated[TokenPayload, Depends(require_permission("users:read"))],
    use_case: Annotated[ListUsersUseCase, Depends(_get_list_uc)],
) -> list[UserResponse]:
    tenant_id = _resolve_tenant_id(current_user)
    users = await use_case.execute(tenant_id)
    return [UserResponse.from_entity(u) for u in users]


@router.get(
    "/{uid}",
    response_model=UserResponse,
    summary="Obtener usuario",
    description="Requiere 'users:read' o ser el propio usuario.",
)
async def get_user(
    uid: str,
    current_user: CurrentUser,
    use_case: Annotated[GetUserUseCase, Depends(_get_get_uc)],
) -> UserResponse:
    if not current_user.is_superadmin and current_user.sub != uid:
        if not current_user.has_permission("users:read"):
            raise ForbiddenException("Sin permiso para ver este usuario")
    tenant_id = _resolve_tenant_id(current_user)
    user = await use_case.execute(uid, tenant_id, current_user.is_superadmin)
    return UserResponse.from_entity(user)


@router.patch(
    "/{uid}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Requiere permiso 'users:update'.",
)
async def update_user(
    uid: str,
    body: UpdateUserRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("users:update"))],
    use_case: Annotated[UpdateUserUseCase, Depends(_get_update_uc)],
) -> UserResponse:
    tenant_id = _resolve_tenant_id(current_user)
    fields = body.model_dump(exclude_none=True)
    user = await use_case.execute(
        uid=uid,
        tenant_id=tenant_id,
        fields=fields,
        updated_by=current_user.sub,
        requester_is_superadmin=current_user.is_superadmin,
    )
    return UserResponse.from_entity(user)


@router.delete(
    "/{uid}",
    status_code=204,
    summary="Desactivar usuario",
    description="Soft delete. Requiere permiso 'users:delete'. Deshabilita también en Firebase Auth.",
)
async def deactivate_user(
    uid: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("users:delete"))],
    use_case: Annotated[DeactivateUserUseCase, Depends(_get_deactivate_uc)],
) -> None:
    tenant_id = _resolve_tenant_id(current_user)
    await use_case.execute(uid, tenant_id, deactivated_by=current_user.sub)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_tenant_id(user: TokenPayload) -> str:
    if user.tenant_id:
        return user.tenant_id
    raise ForbiddenException("Se requiere contexto de taller para esta operación")
