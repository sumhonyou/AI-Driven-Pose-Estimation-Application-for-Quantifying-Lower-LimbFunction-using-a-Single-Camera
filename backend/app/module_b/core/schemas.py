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


class ModuleBFeedbackResponse(BaseModel):
    """Stage 6.5: the after-set coaching text. `feedback_source` is surfaced honestly
    (never hidden) so the report always shows which layer actually produced the text."""

    structured_feedback: str | None = None
    rewritten_feedback: str | None = None
    feedback_source: str
    llm_attempted: bool
    provider: str | None = None
    model_version: str | None = None
    disclaimer_version: str | None = None


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
    feedback: ModuleBFeedbackResponse | None = None
    created_at: str | None = None
    # Stage 7.4: "vs last session" trend, populated only by GET /results/{id} (the
    # report-read-back point, mirroring Module A's Stage 7.2 pattern). None for a
    # session with no previous Module B result of the same exercise to compare against.
    trend: dict | None = None
