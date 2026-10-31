"""Readiness check route verifying PostgreSQL connectivity."""
import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.health import ReadinessResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Service and database are ready"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database connection unavailable"},
    },
    summary="Service Readiness Check",
    description="Verifies database connectivity via a lightweight SELECT 1 query.",
)
def get_ready(db: Session = Depends(get_db)):
    """Check database connectivity and return readiness status."""
    try:
        # Perform lightweight connectivity verification
        db.execute(text("SELECT 1"))
        return ReadinessResponse(status="ready", database="connected")
    except Exception as exc:
        logger.error("Database readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected"},
        )
