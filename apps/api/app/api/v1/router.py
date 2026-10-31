"""V1 API Router aggregation."""
from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.ready import router as ready_router
from app.api.v1.routes.imports import router as imports_router
from app.api.v1.routes.demo import router as demo_router
from app.api.v1.routes.merchants import router as merchants_router
from app.api.v1.routes.merchant_reviews import router as merchant_reviews_router
from app.api.v1.routes.merchant_aliases import router as merchant_aliases_router
from app.api.v1.routes.commitments import router as commitments_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(ready_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(demo_router)
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(merchant_reviews_router)
api_v1_router.include_router(merchant_aliases_router)
api_v1_router.include_router(commitments_router)
