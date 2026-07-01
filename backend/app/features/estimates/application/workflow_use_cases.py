from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.estimates.domain.workflow import (
    CLIENT_RESPONDABLE,
    STATUS_ACCEPTED,
    STATUS_CONVERTED,
    STATUS_REJECTED,
    STATUS_SENT,
    STATUS_VIEWED,
    validate_transition,
)
from app.features.estimates.infrastructure.estimate_repository import EstimateRepository
from app.features.estimates.infrastructure.item_repository import EstimateItemRepository
from app.features.qr.domain.entities import PublicToken
from app.features.qr.infrastructure.hmac_signer import encode_token
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository

_BUDGET_TOKEN_TYPE = "budget_access"
_BUDGET_TOKEN_EXPIRY_DAYS = 30


class SendEstimateUseCase:
    """draft → sent. Genera un PublicToken tipo 'budget_access' para el portal."""

    def __init__(
        self,
        estimate_repo: EstimateRepository,
        token_repo: PublicTokenRepository,
    ) -> None:
        self._estimates = estimate_repo
        self._tokens = token_repo

    async def execute(self, tenant_id: str, estimate_id: str, sent_by: str) -> str:
        """Retorna la URL pública para que el cliente vea el presupuesto."""
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        validate_transition(estimate.status, STATUS_SENT)

        now = datetime.now(timezone.utc)
        exp = now + timedelta(days=_BUDGET_TOKEN_EXPIRY_DAYS)
        token_id = str(uuid.uuid4())
        iat_ts = int(now.timestamp())
        exp_ts = int(exp.timestamp())

        raw_token = encode_token(
            resource_id=estimate_id,
            tenant_id=tenant_id,
            token_id=token_id,
            iat=iat_ts,
            exp=exp_ts,
            secret=settings.HMAC_SECRET_KEY,
        )

        public_token = PublicToken(
            id=token_id,
            tenant_id=tenant_id,
            resource_id=estimate_id,
            token_type=_BUDGET_TOKEN_TYPE,
            issued_at=now,
            expires_at=exp,
            created_at=now,
            updated_at=now,
            created_by=sent_by,
            updated_by=sent_by,
        )

        await run_sync(self._tokens.create, public_token)
        await run_sync(
            self._estimates.update,
            estimate_id,
            tenant_id,
            {
                "status": STATUS_SENT,
                "sent_at": now,
                "public_token_id": token_id,
            },
            sent_by,
        )

        return f"{settings.PUBLIC_BASE_URL}/api/v1/public/estimates/{raw_token}"


class ViewEstimateUseCase:
    """Registra que el cliente abrió el presupuesto (sent → viewed)."""

    def __init__(self, estimate_repo: EstimateRepository) -> None:
        self._estimates = estimate_repo

    async def execute(self, estimate_id: str, tenant_id: str) -> None:
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        if estimate.status != STATUS_SENT:
            return  # Idempotente: ya visto o ya respondido
        now = datetime.now(timezone.utc)
        await run_sync(
            self._estimates.update,
            estimate_id,
            tenant_id,
            {"status": STATUS_VIEWED, "viewed_at": now},
            "system",
        )


class RespondEstimateUseCase:
    """Cliente acepta o rechaza el presupuesto a través del portal público."""

    def __init__(
        self,
        estimate_repo: EstimateRepository,
        token_repo: PublicTokenRepository,
    ) -> None:
        self._estimates = estimate_repo
        self._tokens = token_repo

    async def execute(
        self,
        estimate_id: str,
        tenant_id: str,
        token_id: str,
        accepted: bool,
        client_notes: str | None = None,
    ) -> None:
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")

        if estimate.status not in CLIENT_RESPONDABLE:
            raise ConflictException(
                f"El presupuesto no puede ser respondido en estado '{estimate.status}'"
            )

        token = await run_sync(self._tokens.find_by_id, token_id)
        if token is None or not token.is_valid or token.resource_id != estimate_id:
            raise ConflictException("Token inválido o expirado")

        new_status = STATUS_ACCEPTED if accepted else STATUS_REJECTED
        validate_transition(estimate.status, new_status)

        now = datetime.now(timezone.utc)
        await run_sync(
            self._estimates.update,
            estimate_id,
            tenant_id,
            {
                "status": new_status,
                "responded_at": now,
                "client_notes": client_notes,
            },
            "client",
        )


class ConvertEstimateUseCase:
    """accepted → converted. Marca el presupuesto como trabajo iniciado."""

    def __init__(self, estimate_repo: EstimateRepository) -> None:
        self._estimates = estimate_repo

    async def execute(
        self, tenant_id: str, estimate_id: str, converted_by: str
    ) -> None:
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        validate_transition(estimate.status, STATUS_CONVERTED)
        now = datetime.now(timezone.utc)
        await run_sync(
            self._estimates.update,
            estimate_id,
            tenant_id,
            {"status": STATUS_CONVERTED},
            converted_by,
        )


class AddEstimateItemUseCase:
    """Agrega un ítem a un presupuesto en estado draft y recalcula totales."""

    def __init__(
        self,
        estimate_repo: EstimateRepository,
        item_repo: EstimateItemRepository,
    ) -> None:
        self._estimates = estimate_repo
        self._items = item_repo

    async def execute(
        self,
        tenant_id: str,
        estimate_id: str,
        item_data: dict,
        created_by: str,
    ) -> None:
        from app.features.estimates.application.use_cases import (
            _build_item_dict,
            _compute_totals,
        )
        from app.features.estimates.domain.workflow import STATUS_DRAFT

        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        if estimate.status != STATUS_DRAFT:
            raise ConflictException("Solo se pueden agregar ítems en estado 'draft'")

        item_dict = _build_item_dict(item_data, estimate_id, tenant_id, created_by)
        await run_sync(self._items.add_item, estimate_id, item_dict)

        new_subtotal = await run_sync(self._items.sum_subtotals, estimate_id)
        new_count = await run_sync(self._items.count, estimate_id)
        tax_amount = round(new_subtotal * estimate.tax_rate, 2)
        await run_sync(
            self._estimates.update,
            estimate_id,
            tenant_id,
            {
                "subtotal": new_subtotal,
                "tax_amount": tax_amount,
                "total": round(new_subtotal + tax_amount, 2),
                "items_count": new_count,
            },
            created_by,
        )


class RemoveEstimateItemUseCase:
    """Elimina un ítem de un presupuesto en estado draft y recalcula totales."""

    def __init__(
        self,
        estimate_repo: EstimateRepository,
        item_repo: EstimateItemRepository,
    ) -> None:
        self._estimates = estimate_repo
        self._items = item_repo

    async def execute(
        self,
        tenant_id: str,
        estimate_id: str,
        item_id: str,
        updated_by: str,
    ) -> None:
        from app.features.estimates.domain.workflow import STATUS_DRAFT

        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        if estimate.status != STATUS_DRAFT:
            raise ConflictException("Solo se pueden eliminar ítems en estado 'draft'")

        item = await run_sync(self._items.find_by_id, estimate_id, item_id)
        if item is None:
            raise NotFoundException(f"Ítem '{item_id}' no encontrado")

        await run_sync(self._items.delete, estimate_id, item_id)

        new_subtotal = await run_sync(self._items.sum_subtotals, estimate_id)
        new_count = await run_sync(self._items.count, estimate_id)
        tax_amount = round(new_subtotal * estimate.tax_rate, 2)
        await run_sync(
            self._estimates.update,
            estimate_id,
            tenant_id,
            {
                "subtotal": new_subtotal,
                "tax_amount": tax_amount,
                "total": round(new_subtotal + tax_amount, 2),
                "items_count": new_count,
            },
            updated_by,
        )
