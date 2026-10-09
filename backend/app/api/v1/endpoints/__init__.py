from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.traffic import router as traffic_router

__all__ = ["health_router", "traffic_router", "dashboard_router"]

