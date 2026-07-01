from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.exceptions import ForbiddenException
from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
from app.features.templates.application.use_cases import (
    CreateTemplateUseCase,
    DeleteTemplateUseCase,
    GetTemplateUseCase,
    ListTemplatesUseCase,
    UpdateTemplateUseCase,
)
from app.features.templates.infrastructure.template_repository import TemplateRepository
from app.features.templates.presentation.schemas import (
    CreateTemplateRequest,
    TemplateResponse,
    UpdateTemplateRequest,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_repo() -> TemplateRepository:
    return TemplateRepository(db=get_firestore())


def _get_create_uc(repo: Annotated[TemplateRepository, Depends(_get_repo)]) -> CreateTemplateUseCase:
    return CreateTemplateUseCase(repo)


def _get_get_uc(repo: Annotated[TemplateRepository, Depends(_get_repo)]) -> GetTemplateUseCase:
    return GetTemplateUseCase(repo)


def _get_list_uc(repo: Annotated[TemplateRepository, Depends(_get_repo)]) -> ListTemplatesUseCase:
    return ListTemplatesUseCase(repo)


def _get_update_uc(repo: Annotated[TemplateRepository, Depends(_get_repo)]) -> UpdateTemplateUseCase:
    return UpdateTemplateUseCase(repo)


def _get_delete_uc(repo: Annotated[TemplateRepository, Depends(_get_repo)]) -> DeleteTemplateUseCase:
    return DeleteTemplateUseCase(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=TemplateResponse,
    status_code=201,
    summary="Crear plantilla de inspección",
)
async def create_template(
    body: CreateTemplateRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("templates:manage"))],
    use_case: Annotated[CreateTemplateUseCase, Depends(_get_create_uc)],
) -> TemplateResponse:
    template = await use_case.execute(
        tenant_id=_tenant(current_user),
        name=body.name,
        categories=[c.model_dump() for c in body.categories],
        created_by=current_user.sub,
        is_default=body.is_default,
    )
    return TemplateResponse.from_entity(template)


@router.get(
    "/",
    response_model=list[TemplateResponse],
    summary="Listar plantillas (sistema + del taller)",
)
async def list_templates(
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:read"))],
    use_case: Annotated[ListTemplatesUseCase, Depends(_get_list_uc)],
) -> list[TemplateResponse]:
    templates = await use_case.execute(_tenant(current_user))
    return [TemplateResponse.from_entity(t) for t in templates]


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Obtener plantilla",
)
async def get_template(
    template_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:read"))],
    use_case: Annotated[GetTemplateUseCase, Depends(_get_get_uc)],
) -> TemplateResponse:
    template = await use_case.execute(template_id)
    return TemplateResponse.from_entity(template)


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Actualizar plantilla",
)
async def update_template(
    template_id: str,
    body: UpdateTemplateRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("templates:manage"))],
    use_case: Annotated[UpdateTemplateUseCase, Depends(_get_update_uc)],
) -> TemplateResponse:
    template = await use_case.execute(
        template_id=template_id,
        fields=body.model_dump(exclude_none=True),
        updated_by=current_user.sub,
    )
    return TemplateResponse.from_entity(template)


@router.delete(
    "/{template_id}",
    status_code=204,
    summary="Eliminar plantilla (soft delete)",
)
async def delete_template(
    template_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("templates:manage"))],
    use_case: Annotated[DeleteTemplateUseCase, Depends(_get_delete_uc)],
) -> None:
    await use_case.execute(template_id=template_id, deleted_by=current_user.sub)


# ---------------------------------------------------------------------------


def _tenant(user: TokenPayload) -> str:
    if user.tenant_id:
        return user.tenant_id
    raise ForbiddenException("Se requiere contexto de taller")
