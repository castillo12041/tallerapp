from __future__ import annotations

from fastapi import APIRouter

from app.core.rbac import PERMISSIONS, SYSTEM_ROLES
from app.dependencies.auth import CurrentUser

router = APIRouter()


@router.get(
    "/roles",
    summary="Listar roles del sistema",
    description="Devuelve los roles canónicos del sistema con sus permisos por defecto.",
)
async def list_roles(current_user: CurrentUser) -> list[dict]:
    return [
        {
            "code": r["code"],
            "name": r["name"],
            "description": r["description"],
            "is_system": r["is_system"],
            "can_be_assigned": r["can_be_assigned"],
            "display_order": r["display_order"],
            "permissions": r["permissions"],
        }
        for r in SYSTEM_ROLES
    ]


@router.get(
    "/permissions",
    summary="Listar permisos del sistema",
    description="Devuelve el catálogo completo de permisos disponibles, agrupados por módulo.",
)
async def list_permissions(current_user: CurrentUser) -> list[dict]:
    return list(PERMISSIONS)
