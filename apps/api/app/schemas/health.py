"""Health check schema."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health response model."""
    status: str = Field(default="ok", description="Operational status of the service")
    service: str = Field(default="mandatelens-api", description="Service identifier")
    version: str = Field(default="0.1.0", description="Service semantic version")
