"""
Base models for the LightRAG Preprocessing API.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model."""
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SuccessResponse(BaseResponse):
    """Success response model."""
    status: str = Field(default="success", description="Success status")


class ErrorResponse(BaseResponse):
    """Error response model."""
    status: str = Field(default="error", description="Error status")
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthStatus(BaseModel):
    """Health status model."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    services: Dict[str, Dict[str, Any]] = Field(..., description="External service status")
    uptime: float = Field(..., description="Application uptime in seconds")


class ServiceHealth(BaseModel):
    """Individual service health model."""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last health check time")
    error: Optional[str] = Field(None, description="Error message if unhealthy")