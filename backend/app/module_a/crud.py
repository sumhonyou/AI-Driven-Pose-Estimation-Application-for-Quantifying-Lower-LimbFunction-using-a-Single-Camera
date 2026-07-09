"""Persistence for Module A results: writes into existing sessions + module_a_results tables."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import selectinload

from app.db.models import ModuleAResult
from app.db.models import Session as SessionModel
from app.module_a import config


def save_result(
    db: DbSession,
    session: SessionModel,
    engine_result: dict,
    band_result: dict,
    client_attempted_reps: int | None = None,
) -> ModuleAResult:
    """Writes the STS result onto the owning session + upserts the module_a_results row.

    Upsert (update-in-place if a row already exists for this session) rather than
    always inserting: a session may now be analyzed multiple times before it's
    complete (once per live rep-boundary check), and a stray/retried request must
    never produce a second row for the same session.
    """
    metrics = engine_result["metrics"]
    quality = engine_result["quality"]

    session.status = "completed"
    session.score = band_result["score"]
    session.band = band_result["band"]
    session.capture_quality = quality["average_visibility"]
    session.valid_frame_ratio = quality["valid_frame_ratio"]

    metrics_json = {
        **metrics,
        "warning_tags": band_result["warning_tags"],
        "client_attempted_reps": client_attempted_reps,
    }

    result = get_result_by_session(db, session.id)
    if result is None:
        result = ModuleAResult(session_id=session.id)
        db.add(result)

    result.completion_time_sec = metrics["completion_time_sec"]
    result.rep_count = metrics["rep_count"]
    result.score = band_result["score"]
    result.trunk_lean_proxy = metrics["avg_trunk_lean_deg"]
    result.final_band = band_result["band"]
    result.confidence_level = quality["quality_band"]
    result.session_status = band_result["session_status"]
    result.is_partial_score = band_result["is_partial_score"]
    result.metrics_json = metrics_json

    db.add(session)
    db.commit()
    db.refresh(result)
    return result


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


def get_result_by_session(db: DbSession, session_id: UUID) -> ModuleAResult | None:
    return db.scalar(
        select(ModuleAResult).where(ModuleAResult.session_id == session_id)
    )


def list_history(
    db: DbSession, user_id: UUID, exercise_type: str | None, limit: int
) -> list[ModuleAResult]:
    stmt = (
        select(ModuleAResult)
        .join(SessionModel, SessionModel.id == ModuleAResult.session_id)
        .options(selectinload(ModuleAResult.session))
        .where(SessionModel.user_id == user_id)
        .order_by(ModuleAResult.created_at.desc())
        .limit(limit)
    )
    if exercise_type:
        stmt = stmt.where(SessionModel.exercise_type == exercise_type)
    return list(db.scalars(stmt))


def save_landmark_log(db: DbSession, session_id: UUID, frames: list[dict]) -> None:
    """Persists numeric world-landmark coords for the replay harness. Gated by config flag."""
    if not config.ENABLE_LANDMARK_LOGGING:
        return
    from app.db.models import ModuleALandmarkLog

    for i, frame in enumerate(frames):
        db.add(
            ModuleALandmarkLog(
                session_id=session_id,
                frame_index=i,
                timestamp_ms=frame["timestampMs"],
                world_landmarks={"landmarks": frame["worldLandmarks"]},
            )
        )
    db.commit()
