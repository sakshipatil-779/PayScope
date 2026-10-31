"""API v1 route endpoints."""
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.ready import router as ready_router

__all__ = ["health_router", "ready_router"]
