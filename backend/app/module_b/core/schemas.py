"""Shared API inputs for the generic Module B endpoints."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.module_a.core.schemas import FrameIn


class ModuleBAnalyzeRequest(BaseModel):
    """One browser-buffered Module B set routed by exercise code."""

    session_id: UUID
    exercise_code: str = Field(min_length=1, max_length=100)
    frames: list[FrameIn] = Field(default_factory=list)


class ModuleBErrorTagResponse(BaseModel):
    tag: str
    severity: str | None = None
    source: str
    message: str | None = None


class ModuleBResultResponse(BaseModel):
    session_id: UUID
    exercise_code: str
    score: float | None = None
    band: str | None = None
    confidence: float | None = None
    model_version: str | None = None
    feature_schema_version: str | None = None
    q: float | None = None
    metrics: dict = Field(default_factory=dict)
    error_tags: list[ModuleBErrorTagResponse] = Field(default_factory=list)
    created_at: str | None = None
