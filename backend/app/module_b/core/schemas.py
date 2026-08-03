"""Shared API inputs for the generic Module B endpoints."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.module_a.core.schemas import FrameIn


class ModuleBAnalyzeRequest(BaseModel):
    """One browser-buffered Module B set routed by exercise code."""

    session_id: UUID
    exercise_code: str = Field(min_length=1, max_length=100)
    frames: list[FrameIn] = Field(default_factory=list)
    # Optional live-page rep goal chosen after the session row already exists.
    target_rep_count: int | None = Field(default=None, ge=1, le=200)


class ModuleBErrorTagResponse(BaseModel):
    tag: str
    severity: str | None = None
    source: str
    message: str | None = None


class RewrittenFeedbackStructured(BaseModel):
    """Structured feedback rendered by the report: summary plus tip list."""

    summary: str
    tips: list[str] = Field(default_factory=list)


class ModuleBFeedbackResponse(BaseModel):
    """After-set coaching text plus the source that produced it."""

    structured_feedback: str | None = None
    rewritten_feedback: str | None = None
    rewritten_feedback_structured: RewrittenFeedbackStructured | None = None
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
    # Populated only when a previous result for the same exercise exists.
    trend: dict | None = None
