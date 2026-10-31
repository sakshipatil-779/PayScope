"""Health and readiness check schemas."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health response model."""
    status: str = Field(default="ok", description="Operational status of the service")
    service: str = Field(default="mandatelens-api", description="Service identifier")
    version: str = Field(default="0.1.0", description="Service semantic version")


class ReadinessResponse(BaseModel):
    """Readiness response model verifying external dependencies."""
    status: str = Field(default="ready", description="Overall readiness status")
    database: str = Field(default="connected", description="Database connection status")
