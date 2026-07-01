from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.features.clients.domain.entities import Client
from app.features.clients.infrastructure.client_repository import ClientRepository


class CreateClientUseCase:
    def __init__(self, repo: ClientRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        first_name: str,
        last_name: str,
        email: str | None,
        phone: str | None,
        whatsapp: str | None,
        rut: str | None,
        created_by: str,
    ) -> Client:
        now = datetime.now(timezone.utc)
        client = Client(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            email=email,
            phone=phone,
            whatsapp=whatsapp,
            rut=rut,
            vehicle_count=0,
            inspection_count=0,
            total_spent=0.0,
            last_interaction_at=None,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
        await run_sync(self._repo.create, client)
        return client


class GetClientUseCase:
    def __init__(self, repo: ClientRepository) -> None:
        self._repo = repo

    async def execute(self, client_id: str, tenant_id: str) -> Client:
        client = await run_sync(self._repo.find_by_id, client_id, tenant_id)
        if client is None:
            raise NotFoundException(f"Cliente '{client_id}' no encontrado")
        return client


class ListClientsUseCase:
    def __init__(self, repo: ClientRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str, search: str | None = None) -> list[Client]:
        return await run_sync(self._repo.list_by_tenant, tenant_id, search)


class UpdateClientUseCase:
    def __init__(self, repo: ClientRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        client_id: str,
        tenant_id: str,
        fields: dict,
        updated_by: str,
    ) -> Client:
        current = await run_sync(self._repo.find_by_id, client_id, tenant_id)
        if current is None:
            raise NotFoundException(f"Cliente '{client_id}' no encontrado")

        # Recompute full_name when name fields change
        if "first_name" in fields or "last_name" in fields:
            fields["full_name"] = "{} {}".format(
                fields.get("first_name", current.first_name),
                fields.get("last_name", current.last_name),
            )

        await run_sync(self._repo.update, client_id, tenant_id, fields, updated_by)

        updated = await run_sync(self._repo.find_by_id, client_id, tenant_id)
        if updated is None:
            raise NotFoundException(f"Cliente '{client_id}' no encontrado")
        return updated


class DeleteClientUseCase:
    def __init__(self, repo: ClientRepository) -> None:
        self._repo = repo

    async def execute(self, client_id: str, tenant_id: str, deleted_by: str) -> None:
        client = await run_sync(self._repo.find_by_id, client_id, tenant_id)
        if client is None:
            raise NotFoundException(f"Cliente '{client_id}' no encontrado")
        await run_sync(self._repo.soft_delete, client_id, tenant_id, deleted_by)
