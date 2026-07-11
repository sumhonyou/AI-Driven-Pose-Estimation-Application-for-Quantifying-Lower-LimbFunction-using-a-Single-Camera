"""Weight-Bearing Lunge Test (WBLT) REST endpoints — Stage 2 (guided bracket,
both legs, symmetry).

Dedicated /api/wblt/* routes because the dual-output (distance + angle) contract
differs from the shared single-buffer /api/module-a/analyze -- built on the same
infrastructure though (auth, ownership check, landmark logging), mirroring
app/module_a/sls/router.py.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.module_a.core.crud import save_landmark_log
from app.module_a.wblt import analysis, config, crud
from app.module_a.wblt.schemas import (WbltAnalyzeRequest,
                                       WbltAttemptResultResponse,
                                       WbltBracketStateResponse,
                                       WbltConfigResponse,
                                       WbltSessionSummaryResponse)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wblt", tags=["weight-bearing-lunge-test"])


def _get_owned_session(db: DbSession, session_id: UUID, user_id: UUID) -> SessionModel:
    session = db.scalar(
        select(SessionModel).where(
            SessionModel.id == session_id, SessionModel.user_id == user_id
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return session


def _existing_legs(session: SessionModel) -> dict:
    if session.module_a_result is None:
        return {}
    metrics = dict(session.module_a_result.metrics_json or {})
    return dict(metrics.get("legs") or {})


@router.get("/config", response_model=WbltConfigResponse)
def get_config() -> WbltConfigResponse:
    """Serves WBLT_CONFIG so live frontend feedback matches the official analysis (§10)."""
    return WbltConfigResponse(**config.WBLT_CONFIG)


@router.get(
    "/session/{session_id}/bracket/{leg}", response_model=WbltBracketStateResponse
)
def get_bracket_state(
    session_id: UUID,
    leg: str,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WbltBracketStateResponse:
    """Next target distance + attempt number for this leg, fetched before capture.

    Needed even for attempt 1: the seed distance comes from the account's
    exact_age/sex resolved server-side (§1.1), never sent by the client.
    """
    if leg not in ("left", "right"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="leg must be 'left' or 'right'",
        )
    session = _get_owned_session(db, session_id, current_user.id)
    legs = _existing_legs(session)
    attempts = (legs.get(leg) or {}).get("attempts", [])

    profile = current_user.profile
    exact_age = profile.exact_age if profile else None
    gender = profile.gender if profile else None
    seed_cm = analysis.resolve_seed_cm(exact_age, gender)

    bracket = analysis.bracket_state(attempts, seed_cm)
    return WbltBracketStateResponse(
        leg=leg,
        attempt_number=bracket["attempt_number"],
        next_target_distance_cm=bracket["next_target_distance_cm"],
        leg_complete=bracket["leg_complete"],
        seed_available=seed_cm is not None,
    )


@router.post("/analyze", response_model=WbltAttemptResultResponse)
def analyze_attempt(
    payload: WbltAnalyzeRequest,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WbltAttemptResultResponse:
    """Analyzes one buffered attempt, appends it to the leg's bracket, persists,
    and returns the official result plus the next bracket step.

    `ageband_sex` is resolved here from the authenticated user's stored
    profile, never accepted from the client, so a tampered/stale client value
    can never affect the band.
    """
    session = _get_owned_session(db, payload.sessionId, current_user.id)
    frames = [f.model_dump() for f in payload.frames]
    logger.info(
        "wblt analyze session=%s leg=%s target=%scm touched=%s frames=%d",
        payload.sessionId,
        payload.leg,
        payload.targetDistanceCm,
        payload.touched,
        len(frames),
    )

    profile = current_user.profile
    exact_age = profile.exact_age if profile else None
    gender = profile.gender if profile else None

    attempt = analysis.analyze_attempt(
        frames,
        payload.leg,
        payload.targetDistanceCm,
        payload.touched,
        exact_age,
        gender,
    )

    legs = _existing_legs(session)
    prior_attempts = (legs.get(payload.leg) or {}).get("attempts", [])

    if attempt["q_limiting_factor"] is not None:
        # §8 Q gate: this capture wasn't reliable enough to trust at all --
        # doesn't count as a bracket attempt. Ask for a retry at the SAME
        # target/slot rather than silently stepping the bracket on data that
        # might not reflect the person's real range (or touch) at all.
        save_landmark_log(db, session.id, frames)
        existing_leg_summary = analysis.summarize_leg(prior_attempts)
        session_summary = analysis.compute_session_summary(legs)
        logger.info(
            "wblt low-Q retry session=%s leg=%s target=%scm limiting=%s q=%.2f",
            payload.sessionId,
            payload.leg,
            payload.targetDistanceCm,
            attempt["q_limiting_factor"],
            attempt["q"],
        )
        return WbltAttemptResultResponse(
            session_id=session.id,
            leg=attempt["leg"],
            target_distance_cm=attempt["target_distance_cm"],
            touched=attempt["touched"],
            heel_lift_detected=attempt["heel_lift_detected"],
            attempt_valid=attempt["attempt_valid"],
            valid_touch=False,
            theta_peak_deg=attempt["theta_peak_deg"],
            distance_cm=None,
            band=None,
            score_0_10=None,
            borderline=False,
            q=attempt["q"],
            capture_quality_band=attempt["quality"]["quality_band"],
            valid_frame_ratio=attempt["quality"]["valid_frame_ratio"],
            session_status="low_confidence",
            warning_tags=attempt["warning_tags"],
            persisted=False,
            attempt_number=len(prior_attempts) + 1,
            next_target_distance_cm=payload.targetDistanceCm,
            leg_complete=False,
            leg_best_distance_cm=existing_leg_summary["best_distance_cm"],
            leg_band=existing_leg_summary["band"],
            leg_angle_deg=existing_leg_summary["leg_angle_deg"],
            both_legs_done=session_summary["both_legs_done"],
        )

    new_attempts = prior_attempts + [attempt]
    leg_summary = analysis.summarize_leg(new_attempts)
    legs[payload.leg] = leg_summary

    symmetry = analysis.compute_symmetry(legs)
    session_summary = analysis.compute_session_summary(legs)
    quality = analysis.aggregate_quality(legs)
    profile_snapshot = analysis.resolve_profile_snapshot(exact_age, gender)
    agreement_pairs = analysis.compute_agreement_pairs(legs)

    crud.save_wblt_session(
        db,
        session,
        legs=legs,
        symmetry=symmetry,
        session_summary=session_summary,
        profile=profile_snapshot,
        agreement_pairs=agreement_pairs,
        avg_visibility=quality["average_visibility"],
        valid_frame_ratio=quality["valid_frame_ratio"],
        confidence_level=quality["quality_band"],
    )
    save_landmark_log(db, session.id, frames)
    logger.info(
        "wblt result session=%s leg=%s attempt=%d valid_touch=%s band=%s "
        "leg_complete=%s both_legs_done=%s",
        payload.sessionId,
        payload.leg,
        len(new_attempts),
        attempt["valid_touch"],
        attempt["band"],
        leg_summary["leg_complete"],
        session_summary["both_legs_done"],
    )

    return WbltAttemptResultResponse(
        session_id=session.id,
        leg=attempt["leg"],
        target_distance_cm=attempt["target_distance_cm"],
        touched=attempt["touched"],
        heel_lift_detected=attempt["heel_lift_detected"],
        attempt_valid=attempt["attempt_valid"],
        valid_touch=attempt["valid_touch"],
        theta_peak_deg=attempt["theta_peak_deg"],
        distance_cm=attempt["distance_cm"],
        band=attempt["band"],
        score_0_10=attempt["score_0_10"],
        borderline=attempt["borderline"],
        q=attempt["q"],
        capture_quality_band=attempt["quality"]["quality_band"],
        valid_frame_ratio=attempt["quality"]["valid_frame_ratio"],
        session_status=attempt["session_status"],
        warning_tags=attempt["warning_tags"],
        persisted=True,
        # Next bracket slot (or completed n) — same semantics as GET /bracket
        # and summarize_leg; clients use this for the following attempt label.
        attempt_number=leg_summary["attempt_number"],
        next_target_distance_cm=leg_summary["next_target_distance_cm"],
        leg_complete=leg_summary["leg_complete"],
        leg_best_distance_cm=leg_summary["best_distance_cm"],
        leg_band=leg_summary["band"],
        leg_angle_deg=leg_summary["leg_angle_deg"],
        both_legs_done=session_summary["both_legs_done"],
    )


@router.get("/session/{session_id}", response_model=WbltSessionSummaryResponse)
def get_session_summary(
    session_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WbltSessionSummaryResponse:
    """Full both-legs session summary for the report/dashboard."""
    session = _get_owned_session(db, session_id, current_user.id)
    if session.module_a_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No WBLT result yet"
        )
    metrics = dict(session.module_a_result.metrics_json or {})
    legs = metrics.get("legs") or {}
    if not legs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No WBLT result yet"
        )

    symmetry = metrics.get("symmetry") or {"asym_deg": None, "status": None}
    session_summary = analysis.compute_session_summary(legs)
    profile_snapshot = metrics.get("profile")
    agreement_pairs = metrics.get("agreement_pairs") or []
    captured_at = (metrics.get("session_summary") or {}).get("captured_at")

    previous_legs = crud.get_previous_wblt_legs(db, current_user.id, session.id)
    trend = analysis.compute_trend(legs, previous_legs)

    warning_tags: list[str] = []
    for leg_summary in legs.values():
        for attempt in leg_summary.get("attempts", []):
            for tag in attempt.get("warning_tags", []):
                if tag not in warning_tags:
                    warning_tags.append(tag)

    return WbltSessionSummaryResponse(
        session_id=session.id,
        legs=legs,
        symmetry=symmetry,
        both_legs_done=session_summary["both_legs_done"],
        session_status=session_summary["session_status"],
        warning_tags=warning_tags,
        profile=profile_snapshot,
        agreement_pairs=agreement_pairs,
        captured_at=captured_at,
        trend=trend,
    )
