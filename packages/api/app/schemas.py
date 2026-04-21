"""
Pydantic schemas for request/response models.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Report schemas
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    channel: str = Field(..., max_length=20)
    damage_type: str = Field(..., max_length=50)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    description: str | None = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str | None = None
    reporter_id: str | None = Field(None, max_length=100)
    reporter_name: str | None = Field(None, max_length=200)


class ReportStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|verified|rejected|resolved)$")


class ReportOut(BaseModel):
    id: UUID
    channel: str
    damage_type: str
    severity: str
    status: str
    description: str | None
    latitude: float
    longitude: float
    address: str | None
    reporter_id: str | None
    reporter_name: str | None
    photo_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Map / cluster schemas
# ---------------------------------------------------------------------------

class ClusterOut(BaseModel):
    geohash: str
    count: int
    critical: int
    high: int
    medium: int
    low: int
    centroid_lat: float
    centroid_lng: float


# ---------------------------------------------------------------------------
# Analytics schemas
# ---------------------------------------------------------------------------

class TimelinePoint(BaseModel):
    bucket: str
    total: int
    critical: int
    high: int
    medium: int
    low: int


class SeverityPoint(BaseModel):
    severity: str
    total: int
