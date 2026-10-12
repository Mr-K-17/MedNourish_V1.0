"""Public health check endpoint (Door 2 public route per Architecture.md 6)."""

from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Public health check reporting service status and educational disclaimer."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        disclaimer=settings.EDUCATIONAL_PROTOTYPE_DISCLAIMER,
    )
