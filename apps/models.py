from pydantic import BaseModel

from apps import __version__


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    version: str = __version__
    uptime: float
