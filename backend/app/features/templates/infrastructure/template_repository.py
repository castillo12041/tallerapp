from __future__ import annotations

from datetime import datetime, timezone

from app.features.templates.domain.entities import (
    InspectionTemplate,
    TemplateCategory,
    TemplateItem,
)

_COL = "inspection_templates"


def _to_entity(data: dict, doc_id: str) -> InspectionTemplate:
    categories = tuple(
        TemplateCategory(
            id=cat["id"],
            name=cat["name"],
            order=cat["order"],
            items=tuple(
                TemplateItem(
                    id=it["id"],
                    name=it["name"],
                    order=it["order"],
                    is_required=it.get("isRequired", True),
                )
                for it in cat.get("items", [])
            ),
        )
        for cat in data.get("categories", [])
    )
    raw_del = data.get("deletedAt")
    raw_upd = data.get("updatedAt")
    raw_cre = data.get("createdAt")
    return InspectionTemplate(
        id=doc_id,
        tenant_id=data.get("tenantId"),
        name=data["name"],
        version=data.get("version", 1),
        is_default=data.get("isDefault", False),
        categories=categories,
        total_item_count=data.get("totalItemCount", 0),
        created_at=raw_cre if isinstance(raw_cre, datetime) else datetime.now(timezone.utc),
        updated_at=raw_upd if isinstance(raw_upd, datetime) else datetime.now(timezone.utc),
        created_by=data.get("createdBy", ""),
        updated_by=data.get("updatedBy", ""),
        deleted_at=raw_del if isinstance(raw_del, datetime) else None,
    )


def _categories_to_list(categories: tuple[TemplateCategory, ...]) -> list[dict]:
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "order": cat.order,
            "items": [
                {"id": it.id, "name": it.name, "order": it.order, "isRequired": it.is_required}
                for it in cat.items
            ],
        }
        for cat in categories
    ]


class TemplateRepository:
    def __init__(self, db) -> None:
        self._db = db

    def create(self, template: InspectionTemplate) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(_COL).document(template.id).set({
            "tenantId": template.tenant_id,
            "name": template.name,
            "version": template.version,
            "isDefault": template.is_default,
            "categories": _categories_to_list(template.categories),
            "totalItemCount": template.total_item_count,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": template.created_by,
            "updatedBy": template.updated_by,
            "deletedAt": None,
        })

    def find_by_id(self, template_id: str) -> InspectionTemplate | None:
        doc = self._db.collection(_COL).document(template_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("deletedAt") is not None:
            return None
        return _to_entity(data, doc.id)

    def list_for_tenant(self, tenant_id: str) -> list[InspectionTemplate]:
        """Returns system templates + tenant's own templates, non-deleted."""
        results: list[InspectionTemplate] = []
        col = self._db.collection(_COL)

        # System templates (tenantId == null / None)
        for doc in col.where("tenantId", "==", None).stream():
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                results.append(_to_entity(data, doc.id))

        # Tenant templates
        for doc in col.where("tenantId", "==", tenant_id).stream():
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                results.append(_to_entity(data, doc.id))

        return sorted(results, key=lambda t: t.name)

    def update(self, template_id: str, fields: dict, updated_by: str) -> None:
        mapped: dict = {"updatedAt": datetime.now(timezone.utc), "updatedBy": updated_by}
        if "name" in fields:
            mapped["name"] = fields["name"]
        if "is_default" in fields:
            mapped["isDefault"] = fields["is_default"]
        if "categories" in fields:
            mapped["categories"] = fields["categories"]
            mapped["totalItemCount"] = sum(
                len(cat.get("items", [])) if isinstance(cat, dict) else len(cat.items)
                for cat in fields["categories"]
            )
        self._db.collection(_COL).document(template_id).update(mapped)

    def soft_delete(self, template_id: str, deleted_by: str) -> None:
        self._db.collection(_COL).document(template_id).update({
            "deletedAt": datetime.now(timezone.utc),
            "updatedBy": deleted_by,
        })
