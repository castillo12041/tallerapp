from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ForbiddenException
from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
from app.features.vehicles.application.use_cases import (
    CreateVehicleUseCase,
    DeleteVehicleUseCase,
    GetVehicleUseCase,
    ListVehiclesUseCase,
    UpdateVehicleUseCase,
)
from app.features.vehicles.infrastructure.vehicle_repository import VehicleRepository
from app.features.vehicles.presentation.schemas import (
    CreateVehicleRequest,
    UpdateVehicleRequest,
    VehicleResponse,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_repo() -> VehicleRepository:
    return VehicleRepository(db=get_firestore())


def _get_create_uc(repo: Annotated[VehicleRepository, Depends(_get_repo)]) -> CreateVehicleUseCase:
    return CreateVehicleUseCase(repo)


def _get_get_uc(repo: Annotated[VehicleRepository, Depends(_get_repo)]) -> GetVehicleUseCase:
    return GetVehicleUseCase(repo)


def _get_list_uc(repo: Annotated[VehicleRepository, Depends(_get_repo)]) -> ListVehiclesUseCase:
    return ListVehiclesUseCase(repo)


def _get_update_uc(repo: Annotated[VehicleRepository, Depends(_get_repo)]) -> UpdateVehicleUseCase:
    return UpdateVehicleUseCase(repo)


def _get_delete_uc(repo: Annotated[VehicleRepository, Depends(_get_repo)]) -> DeleteVehicleUseCase:
    return DeleteVehicleUseCase(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=201,
    summary="Registrar vehículo",
    description="La patente se normaliza automáticamente (mayúsculas, sin guiones).",
)
async def create_vehicle(
    body: CreateVehicleRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("vehicles:create"))],
    use_case: Annotated[CreateVehicleUseCase, Depends(_get_create_uc)],
) -> VehicleResponse:
    vehicle = await use_case.execute(
        tenant_id=_tenant(current_user),
        plate=body.plate,
        make=body.make,
        model=body.model,
        created_by=current_user.sub,
        client_id=body.client_id,
        year=body.year,
        color=body.color,
        vin=body.vin,
        engine=body.engine,
        mileage=body.mileage,
        fuel_type=body.fuel_type,
        transmission_type=body.transmission_type,
    )
    return VehicleResponse.from_entity(vehicle)


@router.get(
    "/",
    response_model=list[VehicleResponse],
    summary="Listar vehículos",
    description="Filtrable por `client_id`. Búsqueda por patente, marca, modelo o VIN con `search`.",
)
async def list_vehicles(
    current_user: Annotated[TokenPayload, Depends(require_permission("vehicles:read"))],
    use_case: Annotated[ListVehiclesUseCase, Depends(_get_list_uc)],
    client_id: str | None = Query(None),
    search: str | None = Query(None, min_length=2, max_length=50),
) -> list[VehicleResponse]:
    vehicles = await use_case.execute(_tenant(current_user), client_id=client_id, search=search)
    return [VehicleResponse.from_entity(v) for v in vehicles]


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Obtener vehículo",
)
async def get_vehicle(
    vehicle_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("vehicles:read"))],
    use_case: Annotated[GetVehicleUseCase, Depends(_get_get_uc)],
) -> VehicleResponse:
    vehicle = await use_case.execute(vehicle_id, _tenant(current_user))
    return VehicleResponse.from_entity(vehicle)


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Actualizar vehículo",
)
async def update_vehicle(
    vehicle_id: str,
    body: UpdateVehicleRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("vehicles:update"))],
    use_case: Annotated[UpdateVehicleUseCase, Depends(_get_update_uc)],
) -> VehicleResponse:
    vehicle = await use_case.execute(
        vehicle_id=vehicle_id,
        tenant_id=_tenant(current_user),
        fields=body.model_dump(exclude_none=True),
        updated_by=current_user.sub,
    )
    return VehicleResponse.from_entity(vehicle)


@router.delete(
    "/{vehicle_id}",
    status_code=204,
    summary="Eliminar vehículo",
    description="Soft delete. Las inspecciones históricas se mantienen.",
)
async def delete_vehicle(
    vehicle_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("vehicles:delete"))],
    use_case: Annotated[DeleteVehicleUseCase, Depends(_get_delete_uc)],
) -> None:
    await use_case.execute(vehicle_id, _tenant(current_user), deleted_by=current_user.sub)


# ---------------------------------------------------------------------------


def _tenant(user: TokenPayload) -> str:
    if user.tenant_id:
        return user.tenant_id
    raise ForbiddenException("Se requiere contexto de taller")
