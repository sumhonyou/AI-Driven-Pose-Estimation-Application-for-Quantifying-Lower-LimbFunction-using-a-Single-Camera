"""Persistence for Module A results: writes into existing sessions + module_a_results tables."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import selectinload

from app.db.models import ModuleAResult
from app.db.models import Session as SessionModel
from app.module_a import config


def save_result(
    db: DbSession, session: SessionModel, engine_result: dict, band_result: dict
) -> ModuleAResult:
    """Writes the STS result onto the owning session + a new module_a_results row."""
    metrics = engine_result["metrics"]
    quality = engine_result["quality"]

    session.status = "completed"
    session.score = band_result["score"]
    session.band = band_result["band"]
    session.capture_quality = quality["average_visibility"]
    session.valid_frame_ratio = quality["valid_frame_ratio"]

    result = ModuleAResult(
        session_id=session.id,
        completion_time_sec=metrics["completion_time_sec"],
        rep_count=metrics["rep_count"],
        score=band_result["score"],
        trunk_lean_proxy=metrics["avg_trunk_lean_deg"],
        final_band=band_result["band"],
        confidence_level=quality["quality_band"],
        metrics_json={**metrics, "warning_tags": band_result["warning_tags"]},
    )
    db.add(session)
    db.add(result)
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
