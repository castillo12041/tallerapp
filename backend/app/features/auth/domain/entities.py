from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    TENANTADMIN = "tenantadmin"
    WORKSHOPMANAGER = "workshopmanager"
    INSPECTOR = "inspector"
    MECHANIC = "mechanic"
    RECEPTIONIST = "receptionist"
    CUSTOMER = "customer"


@dataclass(frozen=True)
class AuthUser:
    """
    Proyección del usuario necesaria para el flujo de autenticación.
    Solo contiene los campos requeridos para generar tokens y verificar acceso.
    """

    uid: str
    email: str
    display_name: str
    role: UserRole
    permissions: list[str]
    tenant_id: str | None
    plan: str | None
    is_active: bool

    @property
    def is_superadmin(self) -> bool:
        return self.role == UserRole.SUPERADMIN
