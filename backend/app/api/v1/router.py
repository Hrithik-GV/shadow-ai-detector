from fastapi import APIRouter
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.risks import router as risks_router
from app.api.v1.endpoints.traffic import router as traffic_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(traffic_router, prefix="/traffic", tags=["Traffic"])
api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_v1_router.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
api_v1_router.include_router(risks_router, prefix="/risks", tags=["Risks"])
api_v1_router.include_router(reports_router, prefix="/reports", tags=["Reports"])

