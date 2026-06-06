from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None = None
    created_at: datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    age_group: str | None = None
    gender: str | None = None
    user_type: str | None = None
    focus_area: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    full_name: str | None = None
    age_group: str | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    user_type: str | None = None
    focus_area: str | None = None
    self_reported_note: str | None = None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    age_group: str | None = None
    gender: str | None = None
    height_cm: float | None = Field(default=None, ge=0, le=300)
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    user_type: str | None = None
    focus_area: str | None = None
    self_reported_note: str | None = None


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    mode: str
    description: str | None = None
    view_guidance: str | None = None
    is_active: bool


class SessionStart(BaseModel):
    mode: str
    exercise_code: str
    device_info: str | None = None


class SessionStartResponse(BaseModel):
    session_id: UUID
    status: str


class SessionEnd(BaseModel):
    capture_quality: float | None = Field(default=None, ge=0, le=1)
    valid_frame_ratio: float | None = Field(default=None, ge=0, le=1)


class SessionRead(BaseModel):
    id: UUID
    mode: str
    exercise_code: str
    exercise_name: str
    exercise_type: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str
    capture_quality: float | None = None
    valid_frame_ratio: float | None = None
    score: float | None = None
    band: str | None = None


class DashboardSummary(BaseModel):
    total_sessions: int
    avg_capture_quality: float | None = None
    latest_score: float | None = None
    latest_band: str | None = None
    recent_sessions: list[SessionRead]


class DashboardTrendPoint(BaseModel):
    label: str
    score: float | None = None


class DashboardErrorTag(BaseModel):
    tag_code: str
    severity: str | None = None
    count: int
