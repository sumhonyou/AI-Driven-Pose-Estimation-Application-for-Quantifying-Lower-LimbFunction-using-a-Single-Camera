"""Pydantic request/response models for the Module A analyze endpoint."""

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


class ModuleAResultResponse(BaseModel):
    session_id: UUID
    band: str
    score: float
    metrics: ModuleAMetrics
    warning_tags: list[str]
    capture_quality_band: str
    valid_frame_ratio: float
