"""Pydantic request/response models shared across Module A exercises.

SLS has its own request/response shapes (both-legs contract) — see
app/module_a/sls/schemas.py.
"""

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


class ModuleAResultResponse(BaseModel):
    session_id: UUID
    band: str
    score: float
    # Passthrough dict rather than an exercise-specific metrics model: SLS rows
    # carry a per-leg shape, WBLT carries trial/dorsiflexion fields, and this
    # endpoint is shared across all Module A exercises. The frontend already
    # reads metrics loosely.
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
