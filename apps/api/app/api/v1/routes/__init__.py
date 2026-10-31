"""API v1 route endpoints."""
from .health import router as health_router

__all__ = ["health_router"]
