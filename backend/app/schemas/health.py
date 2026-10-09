from typing import Dict, Optional
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    status: str = Field(..., description="Status of the component: up, down, or not_configured")
    details: Optional[str] = Field(None, description="Detailed diagnostic or error message")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall application status: healthy, degraded, or unhealthy")
    app_name: str
    version: str
    environment: str
    components: Dict[str, ComponentStatus]
