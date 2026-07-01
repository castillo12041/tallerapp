from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.features.templates.domain.entities import (
    InspectionTemplate,
    TemplateCategory,
    TemplateItem,
)
from app.features.templates.infrastructure.template_repository import TemplateRepository


def _count_items(categories: tuple[TemplateCategory, ...]) -> int:
    return sum(len(cat.items) for cat in categories)


class CreateTemplateUseCase:
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        name: str,
        categories: list[dict],
        created_by: str,
        is_default: bool = False,
    ) -> InspectionTemplate:
        now = datetime.now(timezone.utc)
        cats = tuple(
            TemplateCategory(
                id=cat.get("id") or str(uuid.uuid4()),
                name=cat["name"],
                order=cat["order"],
                items=tuple(
                    TemplateItem(
                        id=it.get("id") or str(uuid.uuid4()),
                        name=it["name"],
                        order=it["order"],
                        is_required=it.get("is_required", True),
                    )
                    for it in cat.get("items", [])
                ),
            )
            for cat in categories
        )
        template = InspectionTemplate(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            version=1,
            is_default=is_default,
            categories=cats,
            total_item_count=_count_items(cats),
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
        await run_sync(self._repo.create, template)
        return template


class GetTemplateUseCase:
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(self, template_id: str) -> InspectionTemplate:
        template = await run_sync(self._repo.find_by_id, template_id)
        if template is None:
            raise NotFoundException(f"Plantilla '{template_id}' no encontrada")
        return template


class ListTemplatesUseCase:
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str) -> list[InspectionTemplate]:
        return await run_sync(self._repo.list_for_tenant, tenant_id)


class UpdateTemplateUseCase:
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        template_id: str,
        fields: dict,
        updated_by: str,
    ) -> InspectionTemplate:
        current = await run_sync(self._repo.find_by_id, template_id)
        if current is None:
            raise NotFoundException(f"Plantilla '{template_id}' no encontrada")
        await run_sync(self._repo.update, template_id, fields, updated_by)
        updated = await run_sync(self._repo.find_by_id, template_id)
        if updated is None:
            raise NotFoundException(f"Plantilla '{template_id}' no encontrada")
        return updated


class DeleteTemplateUseCase:
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(self, template_id: str, deleted_by: str) -> None:
        template = await run_sync(self._repo.find_by_id, template_id)
        if template is None:
            raise NotFoundException(f"Plantilla '{template_id}' no encontrada")
        await run_sync(self._repo.soft_delete, template_id, deleted_by)
