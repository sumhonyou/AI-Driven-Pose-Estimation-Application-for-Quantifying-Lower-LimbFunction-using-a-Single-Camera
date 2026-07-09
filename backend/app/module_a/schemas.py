"""Pydantic request/response models for the Module A analyze endpoint."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WorldLandmarkIn(BaseModel):
    x: float
    y: float
    z: float
    visibility: float = 0.0


class FrameIn(BaseModel):
    timestampMs: float
    worldLandmarks: list[WorldLandmarkIn]


class AnalyzeRequest(BaseModel):
    sessionId: UUID
    exerciseType: str
    frames: list[FrameIn] = Field(default_factory=list)
    # UX-only signal from the frontend's live rep-boundary FSM -- not authoritative,
    # only used to surface an "Attempted reps" figure the backend engine can't
    # otherwise know (it only recognizes confirmed/valid reps).
    clientAttemptedReps: int | None = None
    # True only on the 60s-timeout call: persist whatever was captured even
    # though rep_count may be below target. Every rep-boundary call during
    # normal play sends the default False.
    forceFinalize: bool = False


class ModuleAMetrics(BaseModel):
    rep_count: int
    target_rep_count: int
    completion_time_sec: float | None = None
    rep_durations_sec: list[float] = Field(default_factory=list)
    avg_rep_time_sec: float | None = None
    fastest_rep_time_sec: float | None = None
    slowest_rep_time_sec: float | None = None
    knee_rom_deg: float | None = None
    avg_trunk_lean_deg: float | None = None
    max_trunk_lean_deg: float | None = None
    wobble_count: int
    session_duration_sec: float
    stopped_early: bool
    tracked_leg: str | None = None
    client_attempted_reps: int | None = None


class ModuleAResultResponse(BaseModel):
    session_id: UUID
    band: str
    score: float
    # Passthrough dict rather than the STS-specific ModuleAMetrics model: SLS rows
    # carry a per-leg shape that doesn't fit that model, and this endpoint is shared
    # across all Module A exercises. The frontend already reads metrics loosely.
    metrics: dict
    warning_tags: list[str]
    capture_quality_band: str
    valid_frame_ratio: float
    # Completeness/confidence, decoupled from `band` (which only ever describes
    # movement quality, never a tracking/incompleteness problem).
    session_status: Literal["complete", "incomplete", "low_confidence"]
    is_partial_score: bool = False
    # True only when this specific call actually wrote to the database.
    persisted: bool = True


# --- SLS (rebuild) REST models ---


class SlsAnalyzeRequest(BaseModel):
    sessionId: UUID
    leg: Literal["left", "right"]
    frames: list[FrameIn] = Field(default_factory=list)


class SlsLegResultResponse(BaseModel):
    session_id: UUID
    leg: str
    metrics: dict  # this leg's per-leg metrics (holdSeconds, scores, band, ...)
    session_score: float  # combined score across the legs completed so far
    session_band: str
    both_legs_done: bool
    capture_quality_band: str
    valid_frame_ratio: float
    persisted: bool = True


class SlsSupportRequest(BaseModel):
    sessionId: UUID
    usedSupport: Literal["none", "slight", "support"]


class SlsSessionSummaryResponse(BaseModel):
    session_id: UUID
    combined_score: float
    band: str
    used_support: str | None = None
    max_hold_seconds: float
    per_leg: dict
    left_right_hold_difference_seconds: float | None = None
    session_status: str
    warning_tags: list[str] = Field(default_factory=list)
