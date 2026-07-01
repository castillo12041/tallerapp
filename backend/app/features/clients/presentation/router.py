from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ForbiddenException
from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
from app.features.clients.application.use_cases import (
    CreateClientUseCase,
    DeleteClientUseCase,
    GetClientUseCase,
    ListClientsUseCase,
    UpdateClientUseCase,
)
from app.features.clients.infrastructure.client_repository import ClientRepository
from app.features.clients.presentation.schemas import (
    ClientResponse,
    CreateClientRequest,
    UpdateClientRequest,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_repo() -> ClientRepository:
    return ClientRepository(db=get_firestore())


def _get_create_uc(repo: Annotated[ClientRepository, Depends(_get_repo)]) -> CreateClientUseCase:
    return CreateClientUseCase(repo)


def _get_get_uc(repo: Annotated[ClientRepository, Depends(_get_repo)]) -> GetClientUseCase:
    return GetClientUseCase(repo)


def _get_list_uc(repo: Annotated[ClientRepository, Depends(_get_repo)]) -> ListClientsUseCase:
    return ListClientsUseCase(repo)


def _get_update_uc(repo: Annotated[ClientRepository, Depends(_get_repo)]) -> UpdateClientUseCase:
    return UpdateClientUseCase(repo)


def _get_delete_uc(repo: Annotated[ClientRepository, Depends(_get_repo)]) -> DeleteClientUseCase:
    return DeleteClientUseCase(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=201,
    summary="Registrar cliente",
)
async def create_client(
    body: CreateClientRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("clients:create"))],
    use_case: Annotated[CreateClientUseCase, Depends(_get_create_uc)],
) -> ClientResponse:
    client = await use_case.execute(
        tenant_id=_tenant(current_user),
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone=body.phone,
        whatsapp=body.whatsapp,
        rut=body.rut,
        created_by=current_user.sub,
    )
    return ClientResponse.from_entity(client)


@router.get(
    "/",
    response_model=list[ClientResponse],
    summary="Listar clientes",
    description="Soporta búsqueda por nombre, email, RUT o teléfono con el parámetro `search`.",
)
async def list_clients(
    current_user: Annotated[TokenPayload, Depends(require_permission("clients:read"))],
    use_case: Annotated[ListClientsUseCase, Depends(_get_list_uc)],
    search: str | None = Query(None, min_length=2, max_length=100),
) -> list[ClientResponse]:
    clients = await use_case.execute(_tenant(current_user), search=search)
    return [ClientResponse.from_entity(c) for c in clients]


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Obtener cliente",
)
async def get_client(
    client_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("clients:read"))],
    use_case: Annotated[GetClientUseCase, Depends(_get_get_uc)],
) -> ClientResponse:
    client = await use_case.execute(client_id, _tenant(current_user))
    return ClientResponse.from_entity(client)


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Actualizar cliente",
)
async def update_client(
    client_id: str,
    body: UpdateClientRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("clients:update"))],
    use_case: Annotated[UpdateClientUseCase, Depends(_get_update_uc)],
) -> ClientResponse:
    client = await use_case.execute(
        client_id=client_id,
        tenant_id=_tenant(current_user),
        fields=body.model_dump(exclude_none=True),
        updated_by=current_user.sub,
    )
    return ClientResponse.from_entity(client)


@router.delete(
    "/{client_id}",
    status_code=204,
    summary="Eliminar cliente",
    description="Soft delete. Los vehículos e inspecciones asociados se mantienen.",
)
async def delete_client(
    client_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("clients:delete"))],
    use_case: Annotated[DeleteClientUseCase, Depends(_get_delete_uc)],
) -> None:
    await use_case.execute(client_id, _tenant(current_user), deleted_by=current_user.sub)


# ---------------------------------------------------------------------------


def _tenant(user: TokenPayload) -> str:
    if user.tenant_id:
        return user.tenant_id
    raise ForbiddenException("Se requiere contexto de taller")
