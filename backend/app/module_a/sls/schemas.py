"""Pydantic request/response models for the Single-Leg Stance (rebuild) REST endpoints.

Dedicated shapes because the both-legs contract differs from the shared
single-buffer /api/module-a/analyze (see app/module_a/core/schemas.py).
"""

from typing import Literal
from uuid import UUID

from app.module_a.core.schemas import FrameIn
from pydantic import BaseModel, Field


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
