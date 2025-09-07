from typing import Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Optional[dict] = None


class TokenResponse(BaseModel):
    status: str = "success"
    token: str
    user_agent: str
    timestamp: float


class CaptchaResponse(BaseModel):
    status: str = "success"
    solution: str
    confidence: Optional[float] = None
    processing_time: Optional[float] = None


class PirateCaptchaResponse(BaseModel):
    status: str = "success"
    coordinates: list[list[int]]
    confidence: float
    processing_time: Optional[float] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "2.0.0"
    uptime: float
