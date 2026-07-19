"""Thin generic HTTP router for all Module B exercise plugins."""

import dataclasses
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.module_b.core import crud
from app.module_b.core.fusion import fuse_model
from app.module_b.core.model_registry import get_model_bundle
from app.module_b.core.preprocessing import preprocess_world_landmarks
from app.module_b.core.quality import assess_capture_quality
from app.module_b.core.registry import get_exercise
from app.module_b.core.schemas import ModuleBAnalyzeRequest, ModuleBResultResponse

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
    # Quality is assessed on the raw capture (reflects what was actually
    # recorded); segmentation/features run on the preprocessed stream so
    # OneEuroFilter sees the whole session, not a per-rep window (X3/X1).
    quality = assess_capture_quality(frames)
    preprocessed_frames = preprocess_world_landmarks(frames)
    reps = exercise.segment(preprocessed_frames)
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
    # Stage 5.8: the registered trained bundle, keyed by the exercise's own
    # model_key so a future exercise's artifact is picked up without a router change.
    model = get_model_bundle(exercise.model_key)
    fusion = fuse_model(
        rule_scores=rule_scores,
        model=model,
        features=feature_vectors[0],
        q=float(quality["q"]),
        band_policy=exercise.band_policy,
    )
    # Stage 5.12: interpretable fault gates run across EVERY rep (the ML above only
    # scores rep 0). Any failed gate overrides the fused band to Poor with a specific,
    # human-readable reason. Gate-less exercises return None here and are untouched.
    gate_result = exercise.evaluate_fault_gates(reps, feature_vectors)
    if gate_result is not None and not gate_result.all_passed:
        fusion = dataclasses.replace(fusion, band="Poor")
    result = crud.save_result(
        db,
        session=session,
        exercise_code=exercise.code,
        fusion=fusion,
        rule_scores=rule_scores,
        feature_vectors=feature_vectors,
        reps=reps,
        quality=quality,
        error_tags=(_system_error_tags(fusion.flags) + _fault_gate_tags(gate_result)),
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


def _fault_gate_tags(gate_result) -> list[crud.ErrorTagWrite]:
    """Persist Stage 5.12 fault-gate failures as source="rule" tags with reasons.

    Duck-typed (``all_passed``/``failed`` with per-check ``tag``/``message``) so the
    generic core router stays decoupled from any exercise's gate module. Gate-less
    exercises pass None and contribute no tags. One tag per failed gate kind — a fault
    tripped on several reps is surfaced once, not once per rep — kept in a stable order
    so repeated payloads stay byte-identical (X8).
    """
    if gate_result is None or gate_result.all_passed:
        return []
    seen: dict[str, str] = {}
    for check in gate_result.failed:
        seen.setdefault(check.tag, check.message)
    return [
        crud.ErrorTagWrite(
            tag=tag,
            severity="high",
            source="rule",
            message=message,
        )
        for tag, message in sorted(seen.items())
    ]
