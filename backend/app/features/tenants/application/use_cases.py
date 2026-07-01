from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.tenants.domain.entities import Tenant
from app.features.tenants.infrastructure.tenant_repository import TenantRepository


class CreateTenantUseCase:
    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        name: str,
        slug: str,
        rut: str,
        plan_id: str,
        created_by: str,
    ) -> Tenant:
        existing = await run_sync(self._repo.find_by_slug, slug)
        if existing is not None:
            raise ConflictException(f"El slug '{slug}' ya está en uso")

        tenant_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        tenant = Tenant(
            id=tenant_id,
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            rut=rut,
            plan_id=plan_id,
            subscription_status="trialing",
            is_active=True,
            is_suspended=False,
            storage_used_bytes=0,
            inspection_count_this_month=0,
            active_user_count=0,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )

        await run_sync(self._repo.create, tenant)
        return tenant


class GetTenantUseCase:
    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str) -> Tenant:
        tenant = await run_sync(self._repo.find_by_id, tenant_id)
        if tenant is None:
            raise NotFoundException(f"Taller '{tenant_id}' no encontrado")
        return tenant


class UpdateTenantUseCase:
    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str, fields: dict, updated_by: str) -> Tenant:
        tenant = await run_sync(self._repo.find_by_id, tenant_id)
        if tenant is None:
            raise NotFoundException(f"Taller '{tenant_id}' no encontrado")

        await run_sync(self._repo.update, tenant_id, fields, updated_by)

        updated = await run_sync(self._repo.find_by_id, tenant_id)
        if updated is None:
            raise NotFoundException(f"Taller '{tenant_id}' no encontrado")
        return updated


class ListTenantsUseCase:
    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Tenant]:
        return await run_sync(self._repo.list_all)
