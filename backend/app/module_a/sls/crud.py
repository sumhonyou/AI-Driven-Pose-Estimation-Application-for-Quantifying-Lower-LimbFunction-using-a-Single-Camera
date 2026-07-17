"""Persistence for Single-Leg Stance (rebuild) results — incremental per-leg upsert.

See app/module_a/core/crud.py for the shared STS/WBLT one-shot writer and the
exercise-agnostic read/log helpers this reuses.
"""

from sqlalchemy.orm import Session as DbSession

from app.db.models import ModuleAResult
from app.db.models import Session as SessionModel
from app.module_a.core.crud import get_result_by_session


def save_sls_result(
    db: DbSession,
    session: SessionModel,
    *,
    metrics_json: dict,
    score: float,
    band: str,
    capture_quality_band: str,
    avg_visibility: float,
    valid_frame_ratio: float,
    session_status: str,
    is_partial_score: bool,
    both_legs_done: bool,
    best_hold_sec: float | None = None,
    stability_proxy: float | None = None,
) -> ModuleAResult:
    """Upserts the Single-Leg Stance (rebuild) result onto the owning session.

    SLS posts one leg at a time, so this is called incrementally: the per-leg
    JSONB in `metrics_json` accumulates, and the session score/band reflect the
    legs completed so far. Session marked "completed" only once both legs are in.
    Upsert (not insert) so a retried leg replaces its stored result, never dupes.
    """
    session.score = score
    session.band = band
    session.capture_quality = avg_visibility
    session.valid_frame_ratio = valid_frame_ratio
    if both_legs_done:
        session.status = "completed"

    result = get_result_by_session(db, session.id)
    if result is None:
        result = ModuleAResult(session_id=session.id)
        db.add(result)

    result.hold_duration_sec = best_hold_sec
    result.score = score
    result.final_band = band
    result.confidence_level = capture_quality_band
    result.session_status = session_status
    result.is_partial_score = is_partial_score
    result.stability_proxy = stability_proxy
    result.metrics_json = metrics_json

    db.add(session)
    db.commit()
    db.refresh(result)
    return result
