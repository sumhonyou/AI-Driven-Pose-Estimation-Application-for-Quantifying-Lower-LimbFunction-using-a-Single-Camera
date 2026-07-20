from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

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
    # Denormalized like score/band. None for exercises with no rep concept
    # (SLS, WBLT) and for sessions recorded before this field existed.
    rep_count: int | None = None
    # The rep goal the user set before the set, if any -- lets the report show what was
    # aimed for alongside what was attempted. Optional in the UI, so None is normal.
    target_rep_count: int | None = None


# Latest score/band/quality for a single exercise type (dashboard tile).
class ExerciseLatest(BaseModel):
    score: float | None = None
    band: str | None = None
    capture_quality: float | None = None


class DashboardSummary(BaseModel):
    total_sessions: int
    avg_capture_quality: float | None = None
    latest_score: float | None = None
    latest_band: str | None = None
    recent_sessions: list[SessionRead]
    # Per-exercise latest, keyed by exercise_type, so the dashboard can show a
    # tile per exercise instead of one global "latest". Empty for new accounts.
    latest: dict[str, ExerciseLatest] = Field(default_factory=dict)


# One point on an exercise's score/quality/confidence trend.
class TrendPoint(BaseModel):
    session_id: str
    date: datetime
    score: float | None = None
    band: str | None = None
    capture_quality: float | None = None
    confidence: float | None = None  # Module B only; None for Module A
    # Denormalized like score/band (sessions.rep_count). None for exercises with no
    # rep concept (SLS, WBLT). Stage 5.22: lets the frontend chart attempts vs counted
    # reps per session without a second endpoint -- `score` alone can't distinguish a
    # hard session from a short one.
    rep_count: int | None = None


class ExerciseTrend(BaseModel):
    points: list[TrendPoint]
    # No published MDC exists on the 0-10 composite score for ANY exercise, so
    # the score trend never asserts a "meaningful change". WBLT's published MDC
    # (Powden 2015) is on raw distance/angle and is applied per-session in the
    # report, not on this score series. Kept explicit so the UI can render an
    # honest "no meaningful-change threshold" caption uniformly.
    mdc: float | None = None
    mdc_source: Literal["published", "none"] = "none"


class DashboardErrorTag(BaseModel):
    tag_code: str
    severity: str | None = None
    count: int


# Stage 7.3: reminders. Delivery is calendar-link based (Google Calendar URL +
# downloadable .ics), not email/push -- there is no scheduler or email sender in
# this project, per task.md's "keep it simple" note for this stage.
ReminderFrequency = Literal["once", "daily", "mwf", "weekly"]


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    reminder_time: datetime
    frequency: ReminderFrequency | None = None
    # Which exercise this reminder deep-links to when clicked; None for a
    # generic reminder with no specific exercise attached.
    exercise_code: str | None = None


class ReminderUpdate(BaseModel):
    """All optional -- also used to toggle `is_active` on its own."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    reminder_time: datetime | None = None
    frequency: ReminderFrequency | None = None
    exercise_code: str | None = None
    is_active: bool | None = None


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    reminder_time: datetime
    frequency: str | None = None
    is_active: bool
    exercise_code: str | None = None
    last_completed_at: datetime | None = None
    created_at: datetime
    # Computed, not stored: whether this reminder currently needs the user's
    # attention (drives the nav red-dot + dashboard banner).
    is_due: bool
    # Resolved from the exercise catalog at request time (never persisted) so a
    # retired exercise's name doesn't survive as stale text on an old reminder.
    exercise_name: str | None = None
    exercise_mode: str | None = None
    google_calendar_url: str
    ics_url: str
