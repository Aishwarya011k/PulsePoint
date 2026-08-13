"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from app.models import IncidentStatus


# Auth schemas
class UserRegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"


# Target schemas
class TargetCreateRequest(BaseModel):
    """Schema for creating a new target."""
    name: str
    url: str
    check_interval_seconds: int = 300


class TargetResponse(BaseModel):
    """Schema for target response."""
    id: int
    name: str
    url: str
    check_interval_seconds: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TimeSeriesPoint(BaseModel):
    """Schema for a single timeseries point."""
    timestamp: datetime
    response_time_ms: float
    success: bool
    has_failure: bool


class TimeSeriesStats(BaseModel):
    """Schema for timeseries visualization stats."""
    uptime_percentage: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    current_status: str


class TimeSeriesResponse(BaseModel):
    """Schema for timeseries response."""
    points: List[TimeSeriesPoint]
    stats: TimeSeriesStats


class TargetDetailResponse(TargetResponse):
    """Schema for target detail with recent checks."""
    recent_checks: List["CheckResponse"] = []
    is_public: bool = False
    public_slug: Optional[str] = None


class TargetPublicUpdateRequest(BaseModel):
    """Schema for toggling a target's public status."""
    is_public: bool


class DailyUptimeHistoryPoint(BaseModel):
    """Schema for a single uptime history day."""
    date: str
    uptime_percentage: float
    status: str


class PublicStatusResponse(BaseModel):
    """Schema for public target status page data."""
    name: str
    current_status: str
    uptime_last_24h: float
    uptime_last_7d: float
    uptime_last_30d: float
    daily_history: List[DailyUptimeHistoryPoint]


# Check schemas
class CheckResponse(BaseModel):
    """Schema for check result response."""
    id: int
    target_id: int
    status_code: int
    response_time_ms: float
    success: bool
    checked_at: datetime
    
    class Config:
        from_attributes = True


class CheckHistoryResponse(BaseModel):
    """Schema for paginated check history."""
    total: int
    limit: int
    offset: int
    checks: List[CheckResponse]


# Incident schemas
class IncidentResponse(BaseModel):
    """Schema for incident response."""
    id: int
    target_id: int
    status: IncidentStatus
    started_at: datetime
    resolved_at: Optional[datetime] = None
    summary: Optional[str] = None
    
    class Config:
        from_attributes = True


# Update forward references
TargetDetailResponse.model_rebuild()
