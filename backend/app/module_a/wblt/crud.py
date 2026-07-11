"""Persistence for WBLT results — upsert per session, incremental per-attempt.

See app/module_a/core/crud.py for the shared STS one-shot writer and the
exercise-agnostic read/log helpers this reuses. Mirrors app/module_a/sls/crud.py's
incremental per-leg upsert shape, extended one level further (per-attempt within
each leg) for the guided bracket (§4.2).
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.db.models import ModuleAResult
from app.db.models import Session as SessionModel
from app.module_a.core.crud import get_result_by_session, list_history

WBLT_EXERCISE_CODE = "weight_bearing_lunge_test"


def save_wblt_session(
    db: DbSession,
    session: SessionModel,
    *,
    legs: dict,
    symmetry: dict,
    session_summary: dict,
    profile: dict,
    agreement_pairs: list[dict],
    avg_visibility: float,
    valid_frame_ratio: float,
    confidence_level: str,
) -> ModuleAResult:
    """Upserts the WBLT session's full persisted shape (§9).

    Called after every attempt (not just on completion) so a session in
    progress is always readable -- `session_summary["session_status"]`
    distinguishes "still going" (incomplete) from a finished result.
    `captured_at` is stamped once, the first time both legs complete, and
    preserved on every later call so a re-save never rewrites when a session
    actually finished.
    """
    overall_score = session_summary["overall_score"]
    overall_band = session_summary["overall_band"]
    status = session_summary["session_status"]

    session.score = overall_score
    session.band = overall_band
    session.capture_quality = avg_visibility
    session.valid_frame_ratio = valid_frame_ratio
    if session_summary["both_legs_done"]:
        session.status = "completed"

    result = get_result_by_session(db, session.id)
    existing_metrics = dict(result.metrics_json or {}) if result is not None else {}
    existing_summary = existing_metrics.get("session_summary") or {}
    captured_at = existing_summary.get("captured_at")
    if session_summary["both_legs_done"] and not captured_at:
        captured_at = datetime.now(timezone.utc).isoformat()

    metrics_json = {
        "exercise": "wblt",
        "config_version": 1,
        "profile": profile,
        "legs": legs,
        "symmetry": symmetry,
        "agreement_pairs": agreement_pairs,
        "session_summary": {
            "overall_band": overall_band,
            "overall_score": overall_score,
            "both_legs_done": session_summary["both_legs_done"],
            "captured_at": captured_at,
        },
    }

    if result is None:
        result = ModuleAResult(session_id=session.id)
        db.add(result)

    result.score = overall_score
    result.final_band = overall_band or "invalid"
    result.confidence_level = confidence_level
    result.session_status = status
    result.is_partial_score = not session_summary["both_legs_done"]
    result.metrics_json = metrics_json

    db.add(session)
    db.commit()
    db.refresh(result)
    return result


def get_previous_wblt_legs(
    db: DbSession, user_id: UUID, exclude_session_id: UUID
) -> dict | None:
    """§11 Stage 6: the account's most recent OTHER completed WBLT session's
    `legs`, for the trend comparison. "Completed" means both legs finished
    (`captured_at` stamped) -- an in-progress or abandoned session has nothing
    honest to compare against.
    """
    history = list_history(db, user_id, WBLT_EXERCISE_CODE, limit=10)
    for result in history:
        if result.session_id == exclude_session_id:
            continue
        metrics = result.metrics_json or {}
        if not (metrics.get("session_summary") or {}).get("captured_at"):
            continue
        return metrics.get("legs") or {}
    return None
