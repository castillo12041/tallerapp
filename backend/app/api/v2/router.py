from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    tags=["system"],
    summary="Health check v2",
    description="Verifica que la API v2 está operativa.",
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "api": "v2",
    }
