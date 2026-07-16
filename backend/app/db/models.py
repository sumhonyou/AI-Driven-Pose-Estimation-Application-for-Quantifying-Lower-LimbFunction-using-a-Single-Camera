from datetime import datetime
from decimal import Decimal
from uuid import UUID as PyUUID
from uuid import uuid4

from app.db.database import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    # Profile photo as a base64 data URL (e.g. "data:image/png;base64,...").
    # Stored on User (not UserProfile) so it's available from the same /api/auth/me
    # call every page already makes, with no extra request needed to render it.
    avatar_image: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Exact age (collected directly at signup, required alongside gender) --
    # the single source of truth wherever an age is needed, including WBLT's
    # McBride age-band lookup. Replaced the old 3-bucket age_group column.
    exact_age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(50))
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    user_type: Mapped[str | None] = mapped_column(String(50))
    focus_area: Mapped[str | None] = mapped_column(String(50))
    self_reported_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="profile")


class ExerciseCatalog(Base):
    __tablename__ = "exercise_catalog"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    view_guidance: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    sessions: Mapped[list["Session"]] = relationship(back_populates="exercise")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("exercise_catalog.id"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    capture_quality: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    valid_frame_ratio: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    band: Mapped[str | None] = mapped_column(String(50))
    # Denormalized like score/band. NULL for exercises with no rep concept
    # (SLS, WBLT) and for sessions recorded before this column existed.
    rep_count: Mapped[int | None] = mapped_column(Integer)
    device_info: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="sessions")
    exercise: Mapped[ExerciseCatalog] = relationship(back_populates="sessions")
    module_a_result: Mapped["ModuleAResult | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    module_b_result: Mapped["ModuleBResult | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    module_b_error_tags: Mapped[list["ModuleBErrorTag"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    feedback_text: Mapped["FeedbackText | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reminder_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    frequency: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="reminders")


class ModuleAResult(Base):
    __tablename__ = "module_a_results"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    completion_time_sec: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    hold_duration_sec: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    rep_count: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    rom_band: Mapped[str | None] = mapped_column(String(50))
    stability_proxy: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sway_proxy: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    symmetry_proxy: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    trunk_lean_proxy: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    final_band: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_level: Mapped[str | None] = mapped_column(String(50))
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)
    # Completeness/confidence status, decoupled from final_band (movement quality
    # only). Nullable: pre-existing rows from before this column existed have no
    # value here and are inferred at read time instead of being backfilled.
    session_status: Mapped[str | None] = mapped_column(String(50))
    is_partial_score: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped[Session] = relationship(back_populates="module_a_result")


class ModuleALandmarkLog(Base):
    """Raw world-landmark coordinates per frame — numeric only, never video.

    Powers the deterministic replay harness (backend/app/module_a/scripts/replay_session.py).
    Gated by ENABLE_LANDMARK_LOGGING; not written unless enabled.
    """

    __tablename__ = "module_a_landmark_log"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_ms: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    world_landmarks: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ModuleBResult(Base):
    """Hybrid Module B result: queryable summary plus exercise-shaped JSON metrics."""

    __tablename__ = "module_b_results"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    exercise_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    band: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    model_version: Mapped[str | None] = mapped_column(String(100))
    feature_schema_version: Mapped[str | None] = mapped_column(String(20))
    q: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped[Session] = relationship(back_populates="module_b_result")


class ModuleBErrorTag(Base):
    """One queryable Module B tag, attached directly to the owning session."""

    __tablename__ = "module_b_error_tags"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(20))
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped[Session] = relationship(back_populates="module_b_error_tags")


class FeedbackText(Base):
    __tablename__ = "feedback_texts"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    structured_feedback: Mapped[str | None] = mapped_column(Text)
    rewritten_feedback: Mapped[str | None] = mapped_column(Text)
    llm_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    safety_disclaimer: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped[Session] = relationship(back_populates="feedback_text")
