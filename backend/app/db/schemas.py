from datetime import datetime
from uuid import UUID

from pydantic import (BaseModel, ConfigDict, EmailStr, Field, field_validator,
                      model_validator)

# Base64 data URLs inflate ~33% over the raw file; this caps the encoded text
# around ~3MB of original image data, generous for a profile photo.
MAX_AVATAR_DATA_URL_LENGTH = 4_000_000
ALLOWED_AVATAR_MIME_PREFIXES = (
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/jpg;base64,",
    "data:image/webp;base64,",
)


def _validate_avatar_data_url(value: str | None) -> str | None:
    if value is None:
        return value
    if len(value) > MAX_AVATAR_DATA_URL_LENGTH:
        raise ValueError("Image is too large. Please choose a smaller photo.")
    if not value.startswith(ALLOWED_AVATAR_MIME_PREFIXES):
        raise ValueError("Photo must be a PNG, JPEG, or WEBP image.")
    return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None = None
    avatar_image: str | None = None
    created_at: datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    exact_age: int = Field(ge=1, le=120)
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
    avatar_image: str | None = None
    exact_age: int | None = None
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
    avatar_image: str | None = None
    # Omit to leave unchanged (avatar-only updates); reject explicit null clear.
    exact_age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    height_cm: float | None = Field(default=None, ge=0, le=300)
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    user_type: str | None = None
    focus_area: str | None = None
    self_reported_note: str | None = None

    @field_validator("avatar_image")
    @classmethod
    def _check_avatar_image(cls, value: str | None) -> str | None:
        return _validate_avatar_data_url(value)

    @model_validator(mode="after")
    def _reject_cleared_exact_age(self) -> "ProfileUpdate":
        if "exact_age" in self.model_fields_set and self.exact_age is None:
            raise ValueError("exact_age cannot be cleared")
        return self


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
