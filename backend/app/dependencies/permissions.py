from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.dependencies.auth import get_current_user
from app.schemas.auth import TokenPayload

_PLAN_FEATURES: dict[str, set[str]] = {
    "basic": {
        "inspections:basic",
        "reports:basic",
        "clients:manage",
    },
    "professional": {
        "inspections:basic",
        "inspections:advanced",
        "reports:basic",
        "reports:pdf",
        "clients:manage",
        "vehicles:history",
        "qr:generate",
    },
    "premium": {
        "inspections:basic",
        "inspections:advanced",
        "reports:basic",
        "reports:pdf",
        "reports:custom_branding",
        "clients:manage",
        "vehicles:history",
        "qr:generate",
        "integrations:basic",
        "api:access",
    },
    "enterprise": {
        "*",  # Acceso total
    },
}


def require_permission(permission: str) -> Callable:
    """
    Dependencia FastAPI que verifica que el usuario tiene el permiso indicado.

    Uso: Depends(require_permission("inspections:create"))
    Superadmin siempre pasa. Lanza 403 si no tiene el permiso.
    """

    async def _check(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        if not user.has_permission(permission):
            raise ForbiddenException(f"Permiso requerido: {permission}")
        return user

    _check.__name__ = f"require_{permission.replace(':', '_')}"
    return _check


def require_role(*roles: str) -> Callable:
    """
    Dependencia FastAPI que verifica que el usuario tiene alguno de los roles dados.

    Uso: Depends(require_role("tenantadmin", "workshopmanager"))
    Superadmin siempre pasa.
    """

    async def _check(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        if user.is_superadmin:
            return user
        if user.role not in roles:
            raise ForbiddenException(f"Rol requerido: {', '.join(roles)}")
        return user

    _check.__name__ = f"require_role_{'_or_'.join(roles)}"
    return _check


def require_plan_feature(feature: str) -> Callable:
    """
    Dependencia FastAPI que verifica que el plan del tenant incluye la feature.

    Uso: Depends(require_plan_feature("reports:pdf"))
    Superadmin y enterprise siempre pasan (enterprise tiene '*').
    """

    async def _check(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        if user.is_superadmin:
            return user

        plan = user.plan or "basic"
        allowed = _PLAN_FEATURES.get(plan, set())

        if "*" not in allowed and feature not in allowed:
            raise ForbiddenException(
                f"Tu plan '{plan}' no incluye '{feature}'. "
                "Actualiza tu suscripción para acceder a esta función."
            )
        return user

    _check.__name__ = f"require_feature_{feature.replace(':', '_')}"
    return _check


async def require_tenant(
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """Verifica que el usuario pertenece a un tenant (no es un usuario sin tenant asignado)."""
    if not user.has_tenant and not user.is_superadmin:
        raise UnauthorizedException("El usuario no tiene un tenant asignado")
    return user
