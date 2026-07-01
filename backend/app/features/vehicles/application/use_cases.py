from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.vehicles.domain.entities import Vehicle
from app.features.vehicles.infrastructure.vehicle_repository import VehicleRepository


def _normalize_plate(plate: str) -> str:
    """Elimina guiones y espacios, convierte a mayúsculas. 'AB-CD-12' → 'ABCD12'."""
    return plate.upper().replace("-", "").replace(" ", "")


class CreateVehicleUseCase:
    def __init__(self, repo: VehicleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        plate: str,
        make: str,
        model: str,
        created_by: str,
        client_id: str | None = None,
        year: int | None = None,
        color: str | None = None,
        vin: str | None = None,
        engine: str | None = None,
        mileage: int | None = None,
        fuel_type: str | None = None,
        transmission_type: str | None = None,
    ) -> Vehicle:
        normalized_plate = _normalize_plate(plate)

        existing = await run_sync(self._repo.find_by_plate, normalized_plate, tenant_id)
        if existing is not None:
            raise ConflictException(
                f"Ya existe un vehículo con patente '{normalized_plate}' en este taller"
            )

        now = datetime.now(timezone.utc)
        vehicle = Vehicle(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            plate=normalized_plate,
            make=make,
            model=model,
            client_id=client_id,
            year=year,
            color=color,
            vin=vin,
            engine=engine,
            mileage=mileage,
            fuel_type=fuel_type,
            transmission_type=transmission_type,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
        await run_sync(self._repo.create, vehicle)
        return vehicle


class GetVehicleUseCase:
    def __init__(self, repo: VehicleRepository) -> None:
        self._repo = repo

    async def execute(self, vehicle_id: str, tenant_id: str) -> Vehicle:
        vehicle = await run_sync(self._repo.find_by_id, vehicle_id, tenant_id)
        if vehicle is None:
            raise NotFoundException(f"Vehículo '{vehicle_id}' no encontrado")
        return vehicle


class ListVehiclesUseCase:
    def __init__(self, repo: VehicleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        client_id: str | None = None,
        search: str | None = None,
    ) -> list[Vehicle]:
        return await run_sync(self._repo.list_by_tenant, tenant_id, client_id, search)


class UpdateVehicleUseCase:
    def __init__(self, repo: VehicleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        vehicle_id: str,
        tenant_id: str,
        fields: dict,
        updated_by: str,
    ) -> Vehicle:
        vehicle = await run_sync(self._repo.find_by_id, vehicle_id, tenant_id)
        if vehicle is None:
            raise NotFoundException(f"Vehículo '{vehicle_id}' no encontrado")

        if "plate" in fields:
            fields["plate"] = _normalize_plate(fields["plate"])
            if fields["plate"] != vehicle.plate:
                existing = await run_sync(
                    self._repo.find_by_plate, fields["plate"], tenant_id
                )
                if existing is not None:
                    raise ConflictException(
                        f"Ya existe un vehículo con patente '{fields['plate']}'"
                    )

        await run_sync(self._repo.update, vehicle_id, tenant_id, fields, updated_by)

        updated = await run_sync(self._repo.find_by_id, vehicle_id, tenant_id)
        if updated is None:
            raise NotFoundException(f"Vehículo '{vehicle_id}' no encontrado")
        return updated


class DeleteVehicleUseCase:
    def __init__(self, repo: VehicleRepository) -> None:
        self._repo = repo

    async def execute(self, vehicle_id: str, tenant_id: str, deleted_by: str) -> None:
        vehicle = await run_sync(self._repo.find_by_id, vehicle_id, tenant_id)
        if vehicle is None:
            raise NotFoundException(f"Vehículo '{vehicle_id}' no encontrado")
        await run_sync(self._repo.soft_delete, vehicle_id, tenant_id, deleted_by)
