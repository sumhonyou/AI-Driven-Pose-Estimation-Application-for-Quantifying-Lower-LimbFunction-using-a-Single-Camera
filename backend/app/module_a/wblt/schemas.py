"""Pydantic request/response models for the WBLT REST endpoints (Stage 2: guided
bracket, both legs, symmetry).

Dedicated shapes because the dual-output (distance + angle) contract differs from
the shared single-buffer /api/module-a/analyze -- see app/module_a/core/schemas.py.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.module_a.core.schemas import FrameIn


class WbltAnalyzeRequest(BaseModel):
    sessionId: UUID
    leg: Literal["left", "right"]
    targetDistanceCm: float = Field(gt=0, le=60)
    touched: bool
    frames: list[FrameIn] = Field(default_factory=list)


class WbltAttemptResultResponse(BaseModel):
    session_id: UUID
    leg: str
    target_distance_cm: float
    touched: bool
    heel_lift_detected: bool
    attempt_valid: bool
    valid_touch: bool
    theta_peak_deg: float | None = None
    distance_cm: float | None = None
    band: str | None = None
    score_0_10: float | None = None
    borderline: bool = False
    q: float
    capture_quality_band: str
    valid_frame_ratio: float
    session_status: Literal["complete", "incomplete", "low_confidence"]
    warning_tags: list[str] = Field(default_factory=list)
    persisted: bool = True
    # Bracket state after this attempt was recorded (§4.2).
    attempt_number: int
    next_target_distance_cm: float | None = None
    leg_complete: bool
    leg_best_distance_cm: float | None = None
    leg_band: str | None = None
    leg_angle_deg: float | None = None
    both_legs_done: bool


class WbltBracketStateResponse(BaseModel):
    """Fetched before a leg's first attempt so the frontend knows what target to show."""

    leg: str
    attempt_number: int
    next_target_distance_cm: float | None = None
    leg_complete: bool
    seed_available: bool


class WbltLegSummary(BaseModel):
    attempts: list[dict] = Field(default_factory=list)
    best_distance_cm: float | None = None
    band: str | None = None
    score_0_10: float | None = None
    borderline: bool = False
    leg_angle_deg: float | None = None
    floor_flag: bool = False
    leg_complete: bool = False


class WbltSymmetry(BaseModel):
    asym_deg: float | None = None
    status: Literal["symmetric", "asymmetry_flag"] | None = None


class WbltProfileSnapshot(BaseModel):
    """§9: the age/sex the band was actually computed from, snapshotted at
    analysis time -- not re-derived from the account's current profile."""

    exact_age: int | None = None
    age_band_resolved: str | None = None
    sex: Literal["male", "female"] | None = None


class WbltAgreementPair(BaseModel):
    leg: str
    distance_cm: float
    angle_deg: float


class WbltLegTrend(BaseModel):
    """§11 Stage 6: vs the account's previous completed WBLT session, per leg.
    `_meaningful` flags are MDC-suppressed -- a sub-MDC delta is display noise,
    not a real change (see distance_mdc_cm/angle_mdc_deg in WBLT_CONFIG)."""

    distance_delta_cm: float | None = None
    distance_meaningful: bool = False
    angle_delta_deg: float | None = None
    angle_meaningful: bool = False
    previous_band: str | None = None


class WbltSessionSummaryResponse(BaseModel):
    session_id: UUID
    legs: dict[str, WbltLegSummary] = Field(default_factory=dict)
    symmetry: WbltSymmetry = Field(default_factory=WbltSymmetry)
    both_legs_done: bool
    session_status: Literal["complete", "incomplete", "low_confidence"]
    warning_tags: list[str] = Field(default_factory=list)
    profile: WbltProfileSnapshot | None = None
    agreement_pairs: list[WbltAgreementPair] = Field(default_factory=list)
    captured_at: str | None = None
    trend: dict[str, WbltLegTrend | None] = Field(default_factory=dict)


class WbltConfigResponse(BaseModel):
    version: int
    distance_bands: dict
    seed_distance_cm: dict
    attempts_per_leg: int
    bracket_step_cm: float
    bracket_min_distance_cm: float
    fallback_seed_distance_cm: float
    distance_mdc_cm: float
    leg_order: list[str]
    calibration_seconds: float
    heel_min_calibration_frames: int
    heel_lift_tol_ratio: float
    heel_lift_hysteresis_ratio: float
    heel_lift_debounce_frames: int
    min_valid_frames_per_attempt: int
    angle_symmetry_flag_deg: float
    angle_mdc_deg: float
    q_min: float
