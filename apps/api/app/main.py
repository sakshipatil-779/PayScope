"""PayScope FastAPI Application Entry Point."""
from contextlib import asynccontextmanager
import logging
import os
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.router import api_v1_router

logger = logging.getLogger('app.main')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan running automatic database migrations in background."""
    def _run_migrations():
        try:
            from alembic import command
            from alembic.config import Config

            current_dir = os.path.dirname(os.path.abspath(__file__))
            candidate_paths = [
                os.path.abspath(os.path.join(current_dir, '..', 'alembic.ini')),
                os.path.abspath(os.path.join(current_dir, '..', '..', 'alembic.ini')),
                os.path.abspath('alembic.ini'),
                os.path.abspath('apps/api/alembic.ini'),
            ]
            for ini_path in candidate_paths:
                if os.path.exists(ini_path):
                    logger.info('Running database migrations via Alembic from: %s', ini_path)
                    alembic_cfg = Config(ini_path)
                    command.upgrade(alembic_cfg, 'head')
                    logger.info('Database migrations applied successfully.')
                    break
        except Exception as exc:
            logger.info('Database migration on startup note: %s', exc)

    thread = threading.Thread(target=_run_migrations, daemon=True)
    thread.start()
    yield


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Middleware ensuring CORS headers are present on all responses, including 500 errors
    @application.middleware('http')
    async def ensure_cors_and_error_handling(request: Request, call_next):
        origin = request.headers.get('origin')
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception('Unhandled error processing request %s: %s', request.url.path, exc)
            response = JSONResponse(
                status_code=500,
                content={
                    'detail': 'Internal Server Error',
                    'error': str(exc),
                    'path': request.url.path,
                },
            )

        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = '*'
            response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    # Global exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception('Global exception on %s: %s', request.url.path, exc)
        origin = request.headers.get('origin')
        response = JSONResponse(
            status_code=500,
            content={
                'detail': 'Internal Server Error',
                'error': str(exc),
                'path': request.url.path,
            },
        )
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = '*'
            response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    # Set up standard CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_origin_regex=getattr(settings, 'BACKEND_CORS_ORIGIN_REGEX', None),
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    # Root status endpoint for cloud health & quick browser checks
    @application.get('/', tags=['Root'])
    def root():
        return {
            'name': settings.PROJECT_NAME,
            'status': 'healthy',
            'version': settings.VERSION,
            'docs': f'{settings.API_V1_STR}/docs',
            'health': f'{settings.API_V1_STR}/health',
        }

    # Include API routers
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
