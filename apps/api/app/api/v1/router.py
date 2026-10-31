"""V1 API Router aggregation."""
from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.ready import router as ready_router
from app.api.v1.routes.imports import router as imports_router
from app.api.v1.routes.demo import router as demo_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(ready_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(demo_router)
