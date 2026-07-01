from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ConflictException, NotFoundException
from app.core.firebase import get_firestore
from app.core.utils import run_sync
from app.dependencies.permissions import require_permission
from app.features.estimates.application.use_cases import (
    CreateEstimateUseCase,
    DeleteEstimateUseCase,
    GetEstimateUseCase,
    ListEstimatesUseCase,
    UpdateEstimateUseCase,
)
from app.features.estimates.application.workflow_use_cases import (
    AddEstimateItemUseCase,
    ConvertEstimateUseCase,
    RemoveEstimateItemUseCase,
    RespondEstimateUseCase,
    SendEstimateUseCase,
    ViewEstimateUseCase,
)
from app.features.estimates.infrastructure.counter_repository import (
    EstimateCounterRepository,
)
from app.features.estimates.infrastructure.estimate_repository import EstimateRepository
from app.features.estimates.infrastructure.item_repository import EstimateItemRepository
from app.features.estimates.presentation.schemas import (
    AddItemRequest,
    CreateEstimateRequest,
    EstimateItemOut,
    EstimateListOut,
    EstimateOut,
    EstimateWithItemsOut,
    PublicEstimateOut,
    RespondEstimateRequest,
    SendEstimateResponse,
    UpdateEstimateRequest,
    VehicleSnapshotOut,
    ClientSnapshotOut,
)
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.qr.infrastructure.hmac_signer import decode_and_verify_token
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository
from app.features.vehicles.infrastructure.vehicle_repository import VehicleRepository
from app.core.config import settings
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_estimate_repo() -> EstimateRepository:
    return EstimateRepository(db=get_firestore())


def _get_item_repo() -> EstimateItemRepository:
    return EstimateItemRepository(db=get_firestore())


def _get_counter_repo() -> EstimateCounterRepository:
    return EstimateCounterRepository(db=get_firestore())


def _get_vehicle_repo() -> VehicleRepository:
    return VehicleRepository(db=get_firestore())


def _get_inspection_repo() -> InspectionRepository:
    return InspectionRepository(db=get_firestore())


def _get_token_repo() -> PublicTokenRepository:
    return PublicTokenRepository(db=get_firestore())


def _get_create_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    ir: Annotated[EstimateItemRepository, Depends(_get_item_repo)],
    cr: Annotated[EstimateCounterRepository, Depends(_get_counter_repo)],
    vr: Annotated[VehicleRepository, Depends(_get_vehicle_repo)],
    insr: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
) -> CreateEstimateUseCase:
    return CreateEstimateUseCase(er, ir, cr, vr, insr)


def _get_get_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    ir: Annotated[EstimateItemRepository, Depends(_get_item_repo)],
) -> GetEstimateUseCase:
    return GetEstimateUseCase(er, ir)


def _get_list_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
) -> ListEstimatesUseCase:
    return ListEstimatesUseCase(er)


def _get_update_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
) -> UpdateEstimateUseCase:
    return UpdateEstimateUseCase(er)


def _get_delete_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
) -> DeleteEstimateUseCase:
    return DeleteEstimateUseCase(er)


def _get_send_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    tr: Annotated[PublicTokenRepository, Depends(_get_token_repo)],
) -> SendEstimateUseCase:
    return SendEstimateUseCase(er, tr)


def _get_convert_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
) -> ConvertEstimateUseCase:
    return ConvertEstimateUseCase(er)


def _get_add_item_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    ir: Annotated[EstimateItemRepository, Depends(_get_item_repo)],
) -> AddEstimateItemUseCase:
    return AddEstimateItemUseCase(er, ir)


def _get_remove_item_uc(
    er: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    ir: Annotated[EstimateItemRepository, Depends(_get_item_repo)],
) -> RemoveEstimateItemUseCase:
    return RemoveEstimateItemUseCase(er, ir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _map_estimate(estimate, items=None) -> dict:
    vs = estimate.vehicle_snapshot
    cs = estimate.client_snapshot
    base = {
        "id": estimate.id,
        "number": estimate.number,
        "status": estimate.status,
        "tenant_id": estimate.tenant_id,
        "inspection_id": estimate.inspection_id,
        "vehicle_snapshot": VehicleSnapshotOut(
            id=vs.id, plate=vs.plate, make=vs.make, model=vs.model,
            year=vs.year, color=vs.color, vin=vs.vin,
        ),
        "client_snapshot": ClientSnapshotOut(
            id=cs.id, full_name=cs.full_name, email=cs.email,
            phone=cs.phone, rut=cs.rut,
        ) if cs else None,
        "items_count": estimate.items_count,
        "subtotal": estimate.subtotal,
        "tax_rate": estimate.tax_rate,
        "tax_amount": estimate.tax_amount,
        "total": estimate.total,
        "currency": estimate.currency,
        "notes": estimate.notes,
        "valid_until": estimate.valid_until,
        "sent_at": estimate.sent_at,
        "viewed_at": estimate.viewed_at,
        "responded_at": estimate.responded_at,
        "created_at": estimate.created_at,
        "updated_at": estimate.updated_at,
        "created_by": estimate.created_by,
    }
    if items is not None:
        base["items"] = [
            EstimateItemOut(
                id=i.id, estimate_id=i.estimate_id, name=i.name,
                quantity=i.quantity, unit_price=i.unit_price, subtotal=i.subtotal,
                category=i.category, description=i.description,
                inspection_item_id=i.inspection_item_id,
                created_at=i.created_at, updated_at=i.updated_at,
                created_by=i.created_by, updated_by=i.updated_by,
            )
            for i in items
        ]
    return base


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=EstimateWithItemsOut,
    status_code=201,
    summary="Crear presupuesto",
)
async def create_estimate(
    body: CreateEstimateRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[CreateEstimateUseCase, Depends(_get_create_uc)],
    item_repo: Annotated[EstimateItemRepository, Depends(_get_item_repo)],
) -> EstimateWithItemsOut:
    estimate = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        vehicle_id=body.vehicle_id,
        created_by=current_user.sub,
        items_data=[i.model_dump() for i in body.items],
        tax_rate=body.tax_rate,
        inspection_id=body.inspection_id,
        notes=body.notes,
        valid_until=body.valid_until,
        currency=body.currency,
    )
    items = await run_sync(item_repo.list_by_estimate, estimate.id)
    return EstimateWithItemsOut(**_map_estimate(estimate, items))


@router.get(
    "",
    response_model=EstimateListOut,
    summary="Listar presupuestos",
)
async def list_estimates(
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:read"))],
    uc: Annotated[ListEstimatesUseCase, Depends(_get_list_uc)],
    status: str | None = Query(None),
    inspection_id: str | None = Query(None),
) -> EstimateListOut:
    estimates = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        status=status,
        inspection_id=inspection_id,
    )
    items = [EstimateOut(**_map_estimate(e)) for e in estimates]
    return EstimateListOut(items=items, total=len(items))


@router.get(
    "/{estimate_id}",
    response_model=EstimateWithItemsOut,
    summary="Obtener presupuesto con ítems",
)
async def get_estimate(
    estimate_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:read"))],
    uc: Annotated[GetEstimateUseCase, Depends(_get_get_uc)],
) -> EstimateWithItemsOut:
    estimate, items = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
    )
    return EstimateWithItemsOut(**_map_estimate(estimate, items))


@router.patch(
    "/{estimate_id}",
    response_model=EstimateOut,
    summary="Actualizar presupuesto (solo en estado draft)",
)
async def update_estimate(
    estimate_id: str,
    body: UpdateEstimateRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[UpdateEstimateUseCase, Depends(_get_update_uc)],
) -> EstimateOut:
    estimate = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
        updated_by=current_user.sub,
        fields=body.to_fields(),
    )
    return EstimateOut(**_map_estimate(estimate))


@router.delete(
    "/{estimate_id}",
    status_code=204,
    summary="Eliminar presupuesto (solo en estado draft)",
)
async def delete_estimate(
    estimate_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[DeleteEstimateUseCase, Depends(_get_delete_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
        deleted_by=current_user.sub,
    )


# ---------------------------------------------------------------------------
# Item management endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{estimate_id}/items",
    status_code=201,
    summary="Agregar ítem a presupuesto (solo draft)",
)
async def add_item(
    estimate_id: str,
    body: AddItemRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[AddEstimateItemUseCase, Depends(_get_add_item_uc)],
) -> dict:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
        item_data=body.model_dump(),
        created_by=current_user.sub,
    )
    return {"message": "Ítem agregado correctamente"}


@router.delete(
    "/{estimate_id}/items/{item_id}",
    status_code=204,
    summary="Eliminar ítem de presupuesto (solo draft)",
)
async def remove_item(
    estimate_id: str,
    item_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[RemoveEstimateItemUseCase, Depends(_get_remove_item_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
        item_id=item_id,
        updated_by=current_user.sub,
    )


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{estimate_id}/send",
    response_model=SendEstimateResponse,
    summary="Enviar presupuesto al cliente (draft → sent)",
)
async def send_estimate(
    estimate_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[SendEstimateUseCase, Depends(_get_send_uc)],
) -> SendEstimateResponse:
    public_url = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
        sent_by=current_user.sub,
    )
    return SendEstimateResponse(public_url=public_url)


@router.post(
    "/{estimate_id}/convert",
    status_code=204,
    summary="Convertir presupuesto aceptado a trabajo (accepted → converted)",
)
async def convert_estimate(
    estimate_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("estimates:write"))],
    uc: Annotated[ConvertEstimateUseCase, Depends(_get_convert_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        estimate_id=estimate_id,
        converted_by=current_user.sub,
    )


# ---------------------------------------------------------------------------
# Public portal endpoint (sin JWT)
# ---------------------------------------------------------------------------


@router.get(
    "/public/{token}",
    response_model=PublicEstimateOut,
    summary="Ver presupuesto público (cliente)",
    description=(
        "Endpoint público — no requiere autenticación. "
        "Verifica firma HMAC y retorna el presupuesto para que el cliente lo vea. "
        "Registra automáticamente la primera vez que el cliente abre el enlace (sent → viewed)."
    ),
)
async def view_public_estimate(
    token: str,
    estimate_repo: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    item_repo: Annotated[EstimateItemRepository, Depends(_get_item_repo)],
    token_repo: Annotated[PublicTokenRepository, Depends(_get_token_repo)],
) -> PublicEstimateOut:
    payload = decode_and_verify_token(token, settings.HMAC_SECRET_KEY)
    if payload is None:
        raise NotFoundException("Token inválido")

    now_ts = __import__("time").time()
    if payload["exp"] < now_ts:
        raise ConflictException("El enlace ha expirado")

    stored = await run_sync(token_repo.find_by_id, payload["jti"])
    if stored is None or not stored.is_valid or stored.token_type != "budget_access":
        raise ConflictException("Token revocado o no válido")

    estimate_id: str = payload["iid"]
    tenant_id: str = payload["tid"]

    estimate = await run_sync(estimate_repo.find_by_id, estimate_id, tenant_id)
    if estimate is None:
        raise NotFoundException("Presupuesto no encontrado")

    # Registrar apertura idempotentemente (no bloquea si falla)
    view_uc = ViewEstimateUseCase(estimate_repo)
    try:
        await view_uc.execute(estimate_id, tenant_id)
        # Refrescar para obtener estado actualizado
        estimate = await run_sync(estimate_repo.find_by_id, estimate_id, tenant_id) or estimate
    except Exception:
        pass

    items = await run_sync(item_repo.list_by_estimate, estimate_id)

    vs = estimate.vehicle_snapshot
    cs = estimate.client_snapshot
    return PublicEstimateOut(
        number=estimate.number,
        status=estimate.status,
        vehicle_snapshot=VehicleSnapshotOut(
            id=vs.id, plate=vs.plate, make=vs.make, model=vs.model,
            year=vs.year, color=vs.color, vin=vs.vin,
        ),
        client_snapshot=ClientSnapshotOut(
            id=cs.id, full_name=cs.full_name, email=cs.email,
            phone=cs.phone, rut=cs.rut,
        ) if cs else None,
        items=[
            EstimateItemOut(
                id=i.id, estimate_id=i.estimate_id, name=i.name,
                quantity=i.quantity, unit_price=i.unit_price, subtotal=i.subtotal,
                category=i.category, description=i.description,
                inspection_item_id=i.inspection_item_id,
                created_at=i.created_at, updated_at=i.updated_at,
                created_by=i.created_by, updated_by=i.updated_by,
            )
            for i in items
        ],
        subtotal=estimate.subtotal,
        tax_rate=estimate.tax_rate,
        tax_amount=estimate.tax_amount,
        total=estimate.total,
        currency=estimate.currency,
        notes=estimate.notes,
        valid_until=estimate.valid_until,
    )


@router.post(
    "/public/{token}/respond",
    status_code=204,
    summary="Responder presupuesto (cliente acepta o rechaza)",
)
async def respond_public_estimate(
    token: str,
    body: RespondEstimateRequest,
    estimate_repo: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    token_repo: Annotated[PublicTokenRepository, Depends(_get_token_repo)],
) -> None:
    payload = decode_and_verify_token(token, settings.HMAC_SECRET_KEY)
    if payload is None:
        raise NotFoundException("Token inválido")

    now_ts = __import__("time").time()
    if payload["exp"] < now_ts:
        raise ConflictException("El enlace ha expirado")

    stored = await run_sync(token_repo.find_by_id, payload["jti"])
    if stored is None or not stored.is_valid or stored.token_type != "budget_access":
        raise ConflictException("Token revocado o no válido")

    uc = RespondEstimateUseCase(estimate_repo, token_repo)
    await uc.execute(
        estimate_id=payload["iid"],
        tenant_id=payload["tid"],
        token_id=payload["jti"],
        accepted=body.accepted,
        client_notes=body.client_notes,
    )
