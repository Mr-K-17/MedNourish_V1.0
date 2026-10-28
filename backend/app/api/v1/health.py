"""Public health check endpoint (reporting system & DB connectivity safely)."""

from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse
from app.db.session import check_mysql_health, check_mongodb_health

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Public health check reporting service status and educational disclaimer."""
    mysql_status = check_mysql_health()
    mongo_status = check_mongodb_health()

    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        disclaimer=settings.EDUCATIONAL_PROTOTYPE_DISCLAIMER,
        services={
            "mysql": mysql_status,
            "mongodb": mongo_status,
            "firebase_auth_emulator": {
                "host": settings.FIREBASE_AUTH_EMULATOR_HOST,
                "project": settings.FIREBASE_PROJECT_ID,
            },
        },
    )
