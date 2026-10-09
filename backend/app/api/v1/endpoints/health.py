from fastapi import APIRouter, status
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthCheckResponse, ComponentStatus

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Returns the real-time operational status of the application and its components.",
)
def health_check() -> HealthCheckResponse:
    """Check health of application and verify database connectivity if configured."""
    db_check = check_db_connection()
    db_status = ComponentStatus(
        status=db_check["status"],
        details=db_check.get("details"),
    )

    app_status = ComponentStatus(
        status="up",
        details="Service is running and responsive",
    )

    components = {
        "app": app_status,
        "database": db_status,
    }

    # Evaluate overall status based on real component checks
    if db_status.status == "down":
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthCheckResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        components=components,
    )
