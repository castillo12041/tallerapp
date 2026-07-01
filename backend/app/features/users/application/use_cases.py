from __future__ import annotations

from datetime import datetime, timezone
from functools import partial

from firebase_admin import auth as firebase_auth

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.firebase import set_custom_claims
from app.core.rbac import ASSIGNABLE_ROLES, ROLE_PERMISSIONS
from app.core.utils import run_sync
from app.features.users.domain.entities import User
from app.features.users.infrastructure.user_crud_repository import UserCrudRepository


class CreateUserUseCase:
    def __init__(self, repo: UserCrudRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        email: str,
        display_name: str,
        first_name: str,
        last_name: str,
        password: str,
        role: str,
        tenant_id: str,
        plan: str | None,
        phone: str | None,
        created_by: str,
    ) -> User:
        if role not in ASSIGNABLE_ROLES:
            raise ForbiddenException(f"El rol '{role}' no puede asignarse a usuarios")

        try:
            create_fn = partial(
                firebase_auth.create_user,
                email=email,
                display_name=display_name,
                password=password,
                email_verified=False,
                disabled=False,
            )
            firebase_user = await run_sync(create_fn)
        except firebase_auth.EmailAlreadyExistsError:
            raise ConflictException(f"El email '{email}' ya está registrado")

        uid = firebase_user.uid
        permissions = ROLE_PERMISSIONS.get(role, [])
        now = datetime.now(timezone.utc)

        user = User(
            uid=uid,
            email=email,
            display_name=display_name,
            first_name=first_name,
            last_name=last_name,
            role=role,
            permissions=permissions,
            tenant_id=tenant_id,
            plan=plan,
            is_active=True,
            phone=phone,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )

        try:
            await run_sync(self._repo.create, user)
        except Exception:
            await run_sync(firebase_auth.delete_user, uid)
            raise

        claims = {"tenantId": tenant_id, "role": role, "permissions": permissions, "plan": plan}
        await run_sync(set_custom_claims, uid, claims)

        return user


class GetUserUseCase:
    def __init__(self, repo: UserCrudRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, tenant_id: str, requester_is_superadmin: bool) -> User:
        if requester_is_superadmin:
            user = await run_sync(self._repo.find_by_uid, uid)
        else:
            user = await run_sync(self._repo.find_by_uid_in_tenant, uid, tenant_id)

        if user is None:
            raise NotFoundException(f"Usuario '{uid}' no encontrado")
        return user


class ListUsersUseCase:
    def __init__(self, repo: UserCrudRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str) -> list[User]:
        return await run_sync(self._repo.list_by_tenant, tenant_id)


class UpdateUserUseCase:
    def __init__(self, repo: UserCrudRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        uid: str,
        tenant_id: str,
        fields: dict,
        updated_by: str,
        requester_is_superadmin: bool,
    ) -> User:
        if requester_is_superadmin:
            existing = await run_sync(self._repo.find_by_uid, uid)
        else:
            existing = await run_sync(self._repo.find_by_uid_in_tenant, uid, tenant_id)

        if existing is None:
            raise NotFoundException(f"Usuario '{uid}' no encontrado")

        if "role" in fields and fields["role"] not in ASSIGNABLE_ROLES:
            raise ForbiddenException(f"El rol '{fields['role']}' no puede asignarse")

        if "role" in fields:
            fields["permissions"] = ROLE_PERMISSIONS.get(fields["role"], [])

        await run_sync(self._repo.update, uid, fields, updated_by)

        if "role" in fields or "permissions" in fields:
            new_role = fields.get("role", existing.role)
            new_perms = fields.get("permissions", existing.permissions)
            claims = {
                "tenantId": existing.tenant_id,
                "role": new_role,
                "permissions": new_perms,
                "plan": existing.plan,
            }
            await run_sync(set_custom_claims, uid, claims)

        updated = await run_sync(self._repo.find_by_uid, uid)
        if updated is None:
            raise NotFoundException(f"Usuario '{uid}' no encontrado")
        return updated


class DeactivateUserUseCase:
    def __init__(self, repo: UserCrudRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, tenant_id: str, deactivated_by: str) -> None:
        user = await run_sync(self._repo.find_by_uid_in_tenant, uid, tenant_id)
        if user is None:
            raise NotFoundException(f"Usuario '{uid}' no encontrado")

        await run_sync(self._repo.deactivate, uid, deactivated_by)

        disable_fn = partial(firebase_auth.update_user, uid, disabled=True)
        await run_sync(disable_fn)
