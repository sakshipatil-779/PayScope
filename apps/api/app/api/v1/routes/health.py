"""Health check route."""
from fastapi import APIRouter, status
from app.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns operational status, service name, and version of the API."
)
async def get_health() -> HealthResponse:
    """Return API health status."""
    return HealthResponse(
        status="ok",
        service="mandatelens-api",
        version=settings.VERSION,
    )

