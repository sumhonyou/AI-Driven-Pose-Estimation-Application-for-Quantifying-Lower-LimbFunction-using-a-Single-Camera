"""Module A REST endpoints: analyze a finished STS session, then read it back.

SLS and WBLT each have their own dedicated router (app/module_a/sls/router.py,
app/module_a/wblt/router.py) since their contracts (both-legs; dual distance+angle
output) differ from this shared single-buffer analyze endpoint.
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
from app.module_a.core import banding, crud
from app.module_a.core.schemas import AnalyzeRequest, ModuleAResultResponse
from app.module_a.sls import trend as sls_trend
from app.module_a.sts import trend as sts_trend
from app.module_a.sts.engine import run_sts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/module-a", tags=["module-a"])


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


def _run_engine(frames: list[dict], exercise_type: str) -> dict:
    if exercise_type == "sit_to_stand":
        return run_sts(frames)
    else:
        raise ValueError(f"Unknown exercise_type: {exercise_type}")


def _to_response(
    session_id: UUID,
    engine_result: dict,
    band_result: dict,
    persisted: bool,
    client_attempted_reps: int | None = None,
) -> ModuleAResultResponse:
    metrics = {
        **engine_result["metrics"],
        "client_attempted_reps": client_attempted_reps,
    }
    return ModuleAResultResponse(
        session_id=session_id,
        band=band_result["band"],
        score=band_result["score"],
        metrics=metrics,
        warning_tags=band_result["warning_tags"],
        capture_quality_band=engine_result["quality"]["quality_band"],
        valid_frame_ratio=engine_result["quality"]["valid_frame_ratio"],
        session_status=band_result["session_status"],
        is_partial_score=band_result["is_partial_score"],
        persisted=persisted,
    )


@router.post("/analyze", response_model=ModuleAResultResponse)
def analyze_session(
    payload: AnalyzeRequest,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleAResultResponse:
    """Analyzes Module A session from frames (STS or WBLT).

    Called both as a lightweight live-progress check (once per attempted-rep
    boundary, `forceFinalize=False`) and as the call that finalizes the session
    (either naturally, once metrics reach target, or forced via `forceFinalize=True`
    on early end). Persistence only happens once completion threshold is met, so
    a session in progress can be checked repeatedly without writing until complete.
    """
    session = _get_owned_session(db, payload.sessionId, current_user.id)
    if payload.exerciseType not in ("sit_to_stand",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported exercise type",
        )

    frames = [f.model_dump() for f in payload.frames]
    logger.info(
        "analyze session=%s exercise=%s frames=%d forceFinalize=%s",
        payload.sessionId,
        payload.exerciseType,
        len(frames),
        payload.forceFinalize,
    )

    engine_result = _run_engine(frames, payload.exerciseType)
    band_result = banding.compute_band(
        engine_result["metrics"],
        engine_result["quality"],
        exercise_type=payload.exerciseType,
    )

    should_persist = payload.forceFinalize or (
        engine_result["metrics"]["rep_count"]
        >= engine_result["metrics"]["target_rep_count"]
    )

    if should_persist:
        logger.info(
            "result session=%s band=%s score=%s reps=%s status=%s",
            payload.sessionId,
            band_result["band"],
            band_result["score"],
            engine_result["metrics"]["rep_count"],
            band_result["session_status"],
        )
        crud.save_result(
            db,
            session,
            engine_result,
            band_result,
            client_attempted_reps=payload.clientAttemptedReps,
        )
        crud.save_landmark_log(db, session.id, frames)
        logger.info("persisted session=%s", payload.sessionId)

    return _to_response(
        session.id,
        engine_result,
        band_result,
        persisted=should_persist,
        client_attempted_reps=payload.clientAttemptedReps,
    )


def _legacy_session_status(result) -> str:
    """Infers session_status for rows saved before that column existed.

    Response-time inference only -- never mutates the stored row (no backfill).
    """
    if result.session_status:
        return result.session_status
    return "low_confidence" if result.final_band == "invalid" else "complete"


def _compute_trend(
    db: DbSession, session: SessionModel, result, metrics: dict
) -> dict | None:
    """Compute "vs last session" trend for STS/SLS reports."""
    if session.exercise_type == "sit_to_stand":
        previous = crud.get_previous_completed_result(
            db, session.user_id, "sit_to_stand", session.id, before=result.created_at
        )
        previous_data = (
            {
                "score": float(previous.score) if previous.score is not None else None,
                "band": previous.final_band,
                "completion_time_sec": (
                    float(previous.completion_time_sec)
                    if previous.completion_time_sec is not None
                    else None
                ),
            }
            if previous is not None
            else None
        )
        current_data = {
            "score": float(result.score) if result.score is not None else None,
            "band": result.final_band,
            "completion_time_sec": metrics.get("completion_time_sec"),
        }
        return sts_trend.compute_trend(current_data, previous_data)

    if session.exercise_type == "supported_single_leg_stance":
        previous = crud.get_previous_completed_result(
            db,
            session.user_id,
            "supported_single_leg_stance",
            session.id,
            before=result.created_at,
        )
        previous_legs = (
            dict(previous.metrics_json or {}).get("perLeg", {})
            if previous is not None
            else None
        )
        current_legs = metrics.get("perLeg", {})
        return sls_trend.compute_trend(current_legs, previous_legs)

    return None


@router.get("/sessions/{session_id}", response_model=ModuleAResultResponse)
def get_session_result(
    session_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleAResultResponse:
    session = _get_owned_session(db, session_id, current_user.id)
    result = crud.get_result_by_session(db, session_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Module A result yet"
        )

    metrics = dict(result.metrics_json or {})
    warning_tags = metrics.pop("warning_tags", [])
    return ModuleAResultResponse(
        session_id=session.id,
        band=result.final_band,
        score=float(result.score) if result.score is not None else 0.0,
        metrics=metrics,
        warning_tags=warning_tags,
        capture_quality_band=result.confidence_level or "poor",
        valid_frame_ratio=(
            float(session.valid_frame_ratio) if session.valid_frame_ratio else 0.0
        ),
        session_status=_legacy_session_status(result),
        is_partial_score=result.is_partial_score,
        persisted=True,
        trend=_compute_trend(db, session, result, metrics),
    )


@router.get("/history")
def get_history(
    exerciseType: str | None = None,
    limit: int = 20,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ModuleAResultResponse]:
    results = crud.list_history(db, current_user.id, exerciseType, limit)
    responses = []
    for result in results:
        metrics = dict(result.metrics_json or {})
        warning_tags = metrics.pop("warning_tags", [])
        session_ratio = result.session.valid_frame_ratio if result.session else None
        responses.append(
            ModuleAResultResponse(
                session_id=result.session_id,
                band=result.final_band,
                score=float(result.score) if result.score is not None else 0.0,
                metrics=metrics,
                warning_tags=warning_tags,
                capture_quality_band=result.confidence_level or "poor",
                valid_frame_ratio=(
                    float(session_ratio) if session_ratio is not None else 0.0
                ),
                session_status=_legacy_session_status(result),
                is_partial_score=result.is_partial_score,
                persisted=True,
            )
        )
    return responses
