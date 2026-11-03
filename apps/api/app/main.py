"""PayScope FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # Set up CORS middleware for frontend access
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_origin_regex=getattr(settings, "BACKEND_CORS_ORIGIN_REGEX", None),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Root status endpoint for cloud health & quick browser checks
    @application.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "status": "healthy",
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    # Include API routers
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
