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
    metrics: ModuleAMetrics
    warning_tags: list[str]
    capture_quality_band: str
    valid_frame_ratio: float
    # Completeness/confidence, decoupled from `band` (which only ever describes
    # movement quality, never a tracking/incompleteness problem).
    session_status: Literal["complete", "incomplete", "low_confidence"]
    is_partial_score: bool = False
    # True only when this specific call actually wrote to the database.
    persisted: bool = True
