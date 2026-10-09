import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.health import health_check
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.schemas.health import HealthCheckResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    setup_logging()
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]"
    )
    # Ensure database schema is initialized
    try:
        from app.db.base import Base
        from app.db.session import engine
        import app.models.traffic  # noqa: F401 - register models
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.warning(f"Could not automatically initialize database schema: {exc}")

    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """Factory to create and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    cors_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else ["*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from fastapi import Request
    from fastapi.responses import JSONResponse

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception processing {request.method} {request.url.path}: {exc}")
        resp = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occurred.", "error": str(exc)},
        )
        origin = request.headers.get("origin")
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp

    # Direct top-level health check endpoint
    application.add_api_route(
        "/health",
        health_check,
        methods=["GET"],
        response_model=HealthCheckResponse,
        tags=["Health"],
        summary="Application Health Check",
        description="Returns the real-time operational status of the service.",
    )

    # Mount API v1 router
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Mount unversioned /api/traffic endpoint path as specified in the API contract
    from app.api.v1.endpoints.traffic import router as traffic_router
    application.include_router(traffic_router, prefix="/api/traffic", tags=["Traffic"])

    # Mount unversioned /api/dashboard endpoint path for frontend Overview page
    from app.api.v1.endpoints.dashboard import router as dashboard_router
    application.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])

    @application.get("/", tags=["Root"])
    def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
