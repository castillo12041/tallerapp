from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TemplateItem:
    id: str
    name: str
    order: int
    is_required: bool = True


@dataclass(frozen=True)
class TemplateCategory:
    id: str
    name: str
    order: int
    items: tuple[TemplateItem, ...]


@dataclass(frozen=True)
class InspectionTemplate:
    id: str
    tenant_id: str | None  # None = plantilla de sistema (visible a todos)
    name: str
    version: int
    is_default: bool
    categories: tuple[TemplateCategory, ...]
    total_item_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_system(self) -> bool:
        return self.tenant_id is None
