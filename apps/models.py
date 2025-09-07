from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    version: str = "2.0.0"
    uptime: float
