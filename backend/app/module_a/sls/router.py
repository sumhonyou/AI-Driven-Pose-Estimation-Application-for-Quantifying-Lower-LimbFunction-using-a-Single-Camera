"""Single-Leg Stance (rebuild) REST endpoints.

Dedicated /api/sls/* routes because the both-legs contract differs from the shared
single-buffer /api/module-a/analyze. Built on the SAME infrastructure though —
auth (get_current_user), ownership check, crud persistence, and the deterministic
sls.analysis core — so there is no duplicated auth/persistence logic.
"""

import logging
from uuid import UUID

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.module_a.core.crud import save_landmark_log
from app.module_a.sls import analysis, config, crud
from app.module_a.sls.schemas import (
    SlsAnalyzeRequest,
    SlsLegResultResponse,
    SlsSessionSummaryResponse,
    SlsSupportRequest,
)
from app.module_a.sls.scoring import score_to_band
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sls", tags=["single-leg-stance"])


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


def summarize(per_leg: dict, used_support: str | None) -> dict:
    """Builds the session-level summary from whatever legs are present so far.

    Session score = mean of the completed legs' combined scores. Valid (scoreable)
    legs drive the score; a leg that never produced a hold is 'invalid' and excluded
    from the mean but still reported.
    """
    scoreable = {
        leg: m for leg, m in per_leg.items() if m.get("band") not in (None, "invalid")
    }
    if scoreable:
        combined = sum(m["combinedScore"] for m in scoreable.values()) / len(scoreable)
        band = score_to_band(combined)
    else:
        combined = 0.0
        band = "invalid"

    both_done = "left" in per_leg and "right" in per_leg
    lr_diff = None
    if "left" in per_leg and "right" in per_leg:
        lr_diff = round(
            abs(per_leg["left"]["holdSeconds"] - per_leg["right"]["holdSeconds"]), 2
        )

    if not both_done:
        session_status = "incomplete"
    elif band == "invalid":
        session_status = "low_confidence"
    else:
        session_status = "complete"

    warning_tags: list[str] = []
    for m in per_leg.values():
        for tag in m.get("warningTags", []):
            if tag not in warning_tags:
                warning_tags.append(tag)

    best_hold = max((m.get("holdSeconds", 0.0) for m in per_leg.values()), default=0.0)

    return {
        "exercise": "single-leg-stance",
        "maxHoldSeconds": config.SLS_MAX_HOLD_SEC,
        "combinedScore": round(combined, 2),
        "band": band,
        "usedSupport": used_support,
        "perLeg": per_leg,
        "leftRightHoldDifferenceSeconds": lr_diff,
        "session_status": session_status,
        "warning_tags": warning_tags,
        "both_legs_done": both_done,
        "best_hold_sec": best_hold,
    }


@router.post("/analyze", response_model=SlsLegResultResponse)
def analyze_leg(
    payload: SlsAnalyzeRequest,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SlsLegResultResponse:
    """Analyzes one leg's buffered hold, merges it into the session's per-leg result.

    Called once per leg (two per session). Upserts so a retried leg replaces its
    stored result. Persists on every call — the per-leg result is authoritative.
    """
    session = _get_owned_session(db, payload.sessionId, current_user.id)
    frames = [f.model_dump() for f in payload.frames]
    logger.info(
        "sls analyze session=%s leg=%s frames=%d",
        payload.sessionId,
        payload.leg,
        len(frames),
    )

    result = analysis.analyze_leg(frames, payload.leg)
    leg_metrics = result["metrics"]
    quality = result["quality"]

    # Merge this leg into any per-leg data already stored for the session.
    existing = (
        dict(session.module_a_result.metrics_json or {})
        if session.module_a_result
        else {}
    )
    per_leg = dict(existing.get("perLeg") or {})
    per_leg[payload.leg] = leg_metrics
    used_support = existing.get("usedSupport")

    summary = summarize(per_leg, used_support)
    stability = leg_metrics.get("stabilityScore")

    crud.save_sls_result(
        db,
        session,
        metrics_json=summary,
        score=summary["combinedScore"],
        band=summary["band"],
        capture_quality_band=quality["quality_band"],
        avg_visibility=quality["average_visibility"],
        valid_frame_ratio=quality["valid_frame_ratio"],
        session_status=summary["session_status"],
        is_partial_score=not summary["both_legs_done"],
        both_legs_done=summary["both_legs_done"],
        best_hold_sec=summary["best_hold_sec"],
        stability_proxy=stability,
    )
    save_landmark_log(db, session.id, frames)
    logger.info(
        "sls result session=%s leg=%s hold=%ss band=%s",
        payload.sessionId,
        payload.leg,
        leg_metrics["holdSeconds"],
        leg_metrics["band"],
    )

    return SlsLegResultResponse(
        session_id=session.id,
        leg=payload.leg,
        metrics=leg_metrics,
        session_score=summary["combinedScore"],
        session_band=summary["band"],
        both_legs_done=summary["both_legs_done"],
        capture_quality_band=quality["quality_band"],
        valid_frame_ratio=quality["valid_frame_ratio"],
        persisted=True,
    )


@router.post("/support", response_model=SlsSessionSummaryResponse)
def record_support(
    payload: SlsSupportRequest,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SlsSessionSummaryResponse:
    """Stores the post-session support self-report. Never affects scoring."""
    session = _get_owned_session(db, payload.sessionId, current_user.id)
    if session.module_a_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No SLS result yet"
        )

    metrics = dict(session.module_a_result.metrics_json or {})
    per_leg = dict(metrics.get("perLeg") or {})
    # Re-summarize with the support flag; score is untouched (support excluded).
    summary = summarize(per_leg, payload.usedSupport)
    session.module_a_result.metrics_json = summary
    db.add(session.module_a_result)
    db.commit()
    logger.info(
        "sls support session=%s used=%s", payload.sessionId, payload.usedSupport
    )

    return _summary_response(session.id, summary)


@router.get("/session/{session_id}", response_model=SlsSessionSummaryResponse)
def get_session_summary(
    session_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SlsSessionSummaryResponse:
    """Both-leg session summary for the report and dashboard."""
    session = _get_owned_session(db, session_id, current_user.id)
    if session.module_a_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No SLS result yet"
        )
    metrics = dict(session.module_a_result.metrics_json or {})
    return _summary_response(session.id, metrics)


def _summary_response(session_id: UUID, summary: dict) -> SlsSessionSummaryResponse:
    return SlsSessionSummaryResponse(
        session_id=session_id,
        combined_score=summary.get("combinedScore", 0.0),
        band=summary.get("band", "invalid"),
        used_support=summary.get("usedSupport"),
        max_hold_seconds=summary.get("maxHoldSeconds", config.SLS_MAX_HOLD_SEC),
        per_leg=summary.get("perLeg", {}),
        left_right_hold_difference_seconds=summary.get(
            "leftRightHoldDifferenceSeconds"
        ),
        session_status=summary.get("session_status", "incomplete"),
        warning_tags=summary.get("warning_tags", []),
    )
