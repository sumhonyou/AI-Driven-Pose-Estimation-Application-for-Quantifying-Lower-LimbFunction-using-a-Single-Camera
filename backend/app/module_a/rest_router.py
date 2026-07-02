"""Module A REST endpoints: analyze a finished STS session, then read it back."""

from uuid import UUID

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.module_a import banding, crud
from app.module_a.schemas import AnalyzeRequest, ModuleAResultResponse
from app.module_a.session_engine import SessionEngine
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

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


def _to_response(
    session_id: UUID, engine_result: dict, band_result: dict
) -> ModuleAResultResponse:
    return ModuleAResultResponse(
        session_id=session_id,
        band=band_result["band"],
        score=band_result["score"],
        metrics=engine_result["metrics"],
        warning_tags=band_result["warning_tags"],
        capture_quality_band=engine_result["quality"]["quality_band"],
        valid_frame_ratio=engine_result["quality"]["valid_frame_ratio"],
    )


@router.post("/analyze", response_model=ModuleAResultResponse)
def analyze_session(
    payload: AnalyzeRequest,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleAResultResponse:
    session = _get_owned_session(db, payload.sessionId, current_user.id)
    if payload.exerciseType != "sit_to_stand":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only sit_to_stand is supported by Module A analyze so far",
        )

    frames = [f.model_dump() for f in payload.frames]
    logger.info("analyze session=%s frames=%d", payload.sessionId, len(frames))

    engine_result = SessionEngine().run(frames)
    band_result = banding.compute_band(
        engine_result["metrics"], engine_result["quality"]
    )
    logger.info(
        "result session=%s band=%s score=%s reps=%s",
        payload.sessionId,
        band_result["band"],
        band_result["score"],
        engine_result["metrics"]["rep_count"],
    )

    crud.save_result(db, session, engine_result, band_result)
    crud.save_landmark_log(db, session.id, frames)
    logger.info("persisted session=%s", payload.sessionId)

    return _to_response(session.id, engine_result, band_result)


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
            )
        )
    return responses
