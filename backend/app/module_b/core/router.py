"""Thin generic HTTP router for all Module B exercise plugins."""

import logging
from uuid import UUID

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.module_b.core import crud
from app.module_b.core.fusion import fuse_model
from app.module_b.core.model_registry import StubModel
from app.module_b.core.quality import assess_capture_quality
from app.module_b.core.registry import get_exercise
from app.module_b.core.schemas import ModuleBAnalyzeRequest, ModuleBResultResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/module-b", tags=["module-b"])


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


@router.get("/{code}/config")
def get_module_b_config(code: str) -> dict:
    """Serves the selected plugin's config for frontend threshold sync."""
    exercise = get_exercise(code)
    logger.info("module-b config exercise=%s", exercise.code)
    return exercise.config


@router.post("/analyze")
def analyze_module_b_session(
    payload: ModuleBAnalyzeRequest,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleBResultResponse:
    """Run, snapshot and persist one complete Module B set through its plugin."""
    exercise = get_exercise(payload.exercise_code)
    session = _get_owned_session(db, payload.session_id, current_user.id)
    if session.exercise_type != exercise.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session exercise does not match exercise_code",
        )

    frames = [frame.model_dump() for frame in payload.frames]
    logger.info(
        "module-b analyze session=%s exercise=%s frames=%d",
        payload.session_id,
        exercise.code,
        len(frames),
    )
    quality = assess_capture_quality(frames)
    reps = exercise.segment(frames)
    if not reps:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No complete repetitions were detected in this set",
        )
    feature_vectors = [exercise.extract_features(rep) for rep in reps]
    rule_scores = exercise.set_rule_scores(reps, feature_vectors)
    if rule_scores.score is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No rule score is available for this set",
        )
    # Phase 4 deliberately uses a transparent placeholder; Phase 5 replaces
    # this one construction point with the registered trained bundle.
    model = StubModel(rule_score=rule_scores.score)
    fusion = fuse_model(
        rule_scores=rule_scores,
        model=model,
        features=feature_vectors[0],
        q=float(quality["q"]),
    )
    result = crud.save_result(
        db,
        session=session,
        exercise_code=exercise.code,
        fusion=fusion,
        rule_scores=rule_scores,
        feature_vectors=feature_vectors,
        reps=reps,
        quality=quality,
        error_tags=_system_error_tags(fusion.flags),
    )
    summary = crud.result_summary(result, crud.get_error_tags(db, session.id))
    logger.info(
        "module-b result session=%s exercise=%s band=%s score=%.2f q=%.2f",
        session.id,
        exercise.code,
        fusion.band,
        fusion.score,
        fusion.q,
    )
    return ModuleBResultResponse(**summary)


@router.get("/results/{session_id}")
def get_module_b_result(
    session_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleBResultResponse:
    """Read the exact stored Module B snapshot; never recompute a historical grade."""
    session = _get_owned_session(db, session_id, current_user.id)
    exercise = get_exercise(session.exercise_type)
    result = crud.get_result_by_session(db, session.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module B result not found",
        )
    summary = crud.result_summary(result, crud.get_error_tags(db, session.id))
    logger.info(
        "module-b result session=%s exercise=%s model=%s",
        session_id,
        exercise.code,
        result.model_version,
    )
    return ModuleBResultResponse(**summary)


def _system_error_tags(flags: tuple[str, ...]) -> list[crud.ErrorTagWrite]:
    """Persist Phase 4 fusion/capture flags until Stage 6 adds movement taxonomy."""
    severity_by_tag = {
        "low_confidence": "medium",
        "low_capture_quality": "medium",
        "retry_camera_placement": "medium",
    }
    return [
        crud.ErrorTagWrite(
            tag=flag,
            severity=severity_by_tag.get(flag),
            source="system",
        )
        for flag in flags
    ]
