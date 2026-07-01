from fastapi import APIRouter

from app.core.config import settings
from app.features.auth.presentation.router import router as auth_router
from app.features.clients.presentation.router import router as clients_router
from app.features.inspections.presentation.router import router as inspections_router
from app.features.pdf.presentation.router import router as pdf_router
from app.features.estimates.presentation.router import router as estimates_router
from app.features.appointments.presentation.router import router as appointments_router
from app.features.work_orders.presentation.router import router as work_orders_router
from app.features.qr.presentation.router import router as qr_router
from app.features.roles.presentation.router import router as rbac_router
from app.features.templates.presentation.router import router as templates_router
from app.features.tenants.presentation.router import router as tenants_router
from app.features.users.presentation.router import router as users_router
from app.features.vehicles.presentation.router import router as vehicles_router

router = APIRouter()

router.include_router(auth_router,         prefix="/auth",         tags=["auth"])
router.include_router(tenants_router,      prefix="/tenants",      tags=["tenants"])
router.include_router(users_router,        prefix="/users",        tags=["users"])
router.include_router(clients_router,      prefix="/clients",      tags=["clients"])
router.include_router(vehicles_router,     prefix="/vehicles",     tags=["vehicles"])
router.include_router(templates_router,    prefix="/templates",    tags=["templates"])
router.include_router(inspections_router,  prefix="/inspections",  tags=["inspections"])
router.include_router(pdf_router,          prefix="/pdf",           tags=["pdf"])
router.include_router(qr_router,           prefix="/qr",            tags=["qr"])
router.include_router(estimates_router,    prefix="/estimates",     tags=["estimates"])
router.include_router(work_orders_router,  prefix="/work-orders",   tags=["work-orders"])
router.include_router(appointments_router, prefix="/appointments",  tags=["appointments"])
router.include_router(rbac_router,         tags=["rbac"])


@router.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description="Verifica que la API está operativa.",
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "api": "v1",
    }
