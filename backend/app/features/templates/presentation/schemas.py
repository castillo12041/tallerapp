from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.templates.domain.entities import (
    InspectionTemplate,
    TemplateCategory,
    TemplateItem,
)


class TemplateItemRequest(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=120)
    order: int = Field(..., ge=0)
    is_required: bool = True


class TemplateCategoryRequest(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=80)
    order: int = Field(..., ge=0)
    items: list[TemplateItemRequest] = Field(default_factory=list)


class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    categories: list[TemplateCategoryRequest] = Field(..., min_length=1)
    is_default: bool = False


class UpdateTemplateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    is_default: bool | None = None
    categories: list[TemplateCategoryRequest] | None = None


# --- Responses ---

class TemplateItemResponse(BaseModel):
    id: str
    name: str
    order: int
    is_required: bool

    @classmethod
    def from_entity(cls, item: TemplateItem) -> "TemplateItemResponse":
        return cls(id=item.id, name=item.name, order=item.order, is_required=item.is_required)


class TemplateCategoryResponse(BaseModel):
    id: str
    name: str
    order: int
    items: list[TemplateItemResponse]

    @classmethod
    def from_entity(cls, cat: TemplateCategory) -> "TemplateCategoryResponse":
        return cls(
            id=cat.id, name=cat.name, order=cat.order,
            items=[TemplateItemResponse.from_entity(it) for it in cat.items],
        )


class TemplateResponse(BaseModel):
    id: str
    tenant_id: str | None
    name: str
    version: int
    is_default: bool
    is_system: bool
    total_item_count: int
    categories: list[TemplateCategoryResponse]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, t: InspectionTemplate) -> "TemplateResponse":
        return cls(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            version=t.version,
            is_default=t.is_default,
            is_system=t.is_system,
            total_item_count=t.total_item_count,
            categories=[TemplateCategoryResponse.from_entity(c) for c in t.categories],
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
