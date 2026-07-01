from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.exceptions import ForbiddenException
from app.core.firebase import get_firestore
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import require_role
from app.features.tenants.application.use_cases import (
    CreateTenantUseCase,
    GetTenantUseCase,
    ListTenantsUseCase,
    UpdateTenantUseCase,
)
from app.features.tenants.infrastructure.tenant_repository import TenantRepository
from app.features.tenants.presentation.schemas import (
    CreateTenantRequest,
    SubscriptionResponse,
    TenantResponse,
    UpdateTenantRequest,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories — exportadas para override en tests
# ---------------------------------------------------------------------------


def _get_repo() -> TenantRepository:
    return TenantRepository(db=get_firestore())


def _get_create_uc(repo: Annotated[TenantRepository, Depends(_get_repo)]) -> CreateTenantUseCase:
    return CreateTenantUseCase(repo)


def _get_get_uc(repo: Annotated[TenantRepository, Depends(_get_repo)]) -> GetTenantUseCase:
    return GetTenantUseCase(repo)


def _get_update_uc(repo: Annotated[TenantRepository, Depends(_get_repo)]) -> UpdateTenantUseCase:
    return UpdateTenantUseCase(repo)


def _get_list_uc(repo: Annotated[TenantRepository, Depends(_get_repo)]) -> ListTenantsUseCase:
    return ListTenantsUseCase(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=201,
    summary="Crear taller",
    description="Solo superadmin. Registra un nuevo taller en la plataforma.",
)
async def create_tenant(
    body: CreateTenantRequest,
    current_user: Annotated[TokenPayload, Depends(require_role("superadmin"))],
    use_case: Annotated[CreateTenantUseCase, Depends(_get_create_uc)],
) -> TenantResponse:
    tenant = await use_case.execute(
        name=body.name,
        slug=body.slug,
        rut=body.rut,
        plan_id=body.plan_id,
        created_by=current_user.sub,
    )
    return TenantResponse.from_entity(tenant)


@router.get(
    "/",
    response_model=list[TenantResponse],
    summary="Listar talleres",
    description="Solo superadmin. Devuelve todos los talleres activos.",
)
async def list_tenants(
    current_user: Annotated[TokenPayload, Depends(require_role("superadmin"))],
    use_case: Annotated[ListTenantsUseCase, Depends(_get_list_uc)],
) -> list[TenantResponse]:
    tenants = await use_case.execute()
    return [TenantResponse.from_entity(t) for t in tenants]


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Obtener taller",
    description="Superadmin puede ver cualquier taller. Tenantadmin solo ve el suyo.",
)
async def get_tenant(
    tenant_id: str,
    current_user: CurrentUser,
    use_case: Annotated[GetTenantUseCase, Depends(_get_get_uc)],
) -> TenantResponse:
    _assert_tenant_access(current_user, tenant_id)
    tenant = await use_case.execute(tenant_id)
    return TenantResponse.from_entity(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Actualizar taller",
    description="Solo superadmin. Actualiza nombre, plan o estado.",
)
async def update_tenant(
    tenant_id: str,
    body: UpdateTenantRequest,
    current_user: Annotated[TokenPayload, Depends(require_role("superadmin"))],
    use_case: Annotated[UpdateTenantUseCase, Depends(_get_update_uc)],
) -> TenantResponse:
    fields = body.model_dump(exclude_none=True)
    tenant = await use_case.execute(tenant_id, fields, updated_by=current_user.sub)
    return TenantResponse.from_entity(tenant)


@router.get(
    "/{tenant_id}/subscription",
    response_model=SubscriptionResponse,
    summary="Información de suscripción",
    description="Superadmin o tenantadmin del taller. Devuelve plan, estado y métricas de uso.",
)
async def get_subscription(
    tenant_id: str,
    current_user: CurrentUser,
    use_case: Annotated[GetTenantUseCase, Depends(_get_get_uc)],
) -> SubscriptionResponse:
    _assert_tenant_access(current_user, tenant_id)
    tenant = await use_case.execute(tenant_id)
    return SubscriptionResponse.from_entity(tenant)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_tenant_access(user: TokenPayload, tenant_id: str) -> None:
    if user.is_superadmin:
        return
    if not user.has_permission("tenant:read"):
        raise ForbiddenException("Sin permiso para ver configuración del taller")
    if user.tenant_id != tenant_id:
        raise ForbiddenException("Solo puedes acceder a tu propio taller")
