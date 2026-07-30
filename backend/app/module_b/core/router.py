"""Thin generic HTTP router for all Module B exercise plugins."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.module_b.core import crud
from app.module_b.core.feedback import build_structured_feedback
from app.module_b.core.feedback_contract import serialize as serialize_feedback_contract
from app.module_b.core.feedback_safety import check_llm_feedback
from app.module_b.core.feedback_templates import (
    CURRENT_DISCLAIMER_VERSION,
    compose_template,
)
from app.module_b.core.llm_client import GroqClient
from app.module_b.core.model_registry import get_model_bundle
from app.module_b.core.preprocessing import preprocess_world_landmarks
from app.module_b.core.quality import assess_capture_quality
from app.module_b.core.registry import get_exercise
from app.module_b.core.schemas import ModuleBAnalyzeRequest, ModuleBResultResponse
from app.module_b.core.set_scoring import failed_gates_by_rep, score_set
from app.module_b.squat import trend as squat_trend

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
    # Gates run first now: Stage 5.13 folds each rep's gate failures into that rep's own
    # verdict, instead of Stage 5.12's blanket "any gate fails -> the whole set is Poor"
    # override (which condemned a long set for one bad rep and left `score` contradicting
    # the band). Gate-less exercises return None and are unaffected.
    gate_result = exercise.evaluate_fault_gates(reps, feature_vectors)
    set_score = score_set(
        rule_scores=rule_scores,
        model=model,
        feature_vectors=feature_vectors,
        q=float(quality["q"]),
        band_policy=exercise.band_policy,
        failed_gates_by_rep=failed_gates_by_rep(gate_result),
    )
    fusion = set_score.fusion
    result = crud.save_result(
        db,
        session=session,
        exercise_code=exercise.code,
        fusion=fusion,
        rule_scores=rule_scores,
        feature_vectors=feature_vectors,
        reps=reps,
        quality=quality,
        error_tags=_build_error_tags(exercise, fusion, gate_result, rule_scores),
        rep_verdicts=set_score.rep_verdicts,
        target_rep_count=payload.target_rep_count,
    )
    summary = crud.result_summary(result, crud.get_error_tags(db, session.id))
    summary["feedback"] = _build_and_save_feedback(
        db, session_id=session.id, summary=summary
    )
    logger.info(
        "module-b result session=%s exercise=%s band=%s score=%.2f q=%.2f",
        session.id,
        exercise.code,
        fusion.band,
        fusion.score,
        fusion.q,
    )
    return ModuleBResultResponse(**summary)


def _compute_trend(db: DbSession, session: SessionModel, result) -> dict | None:
    """Stage 7.4: "vs last session" trend, mirroring Module A's Stage 7.2 helper."""
    previous = crud.get_previous_result(
        db, session.user_id, result.exercise_code, session.id, before=result.created_at
    )
    previous_data = (
        {
            "score": float(previous.score) if previous.score is not None else None,
            "band": previous.band,
            "rep_count": previous.session.rep_count if previous.session else None,
        }
        if previous is not None
        else None
    )
    current_data = {
        "score": float(result.score) if result.score is not None else None,
        "band": result.band,
        "rep_count": session.rep_count,
    }
    return squat_trend.compute_trend(current_data, previous_data)


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
    # Read the exact stored feedback row, never recompute it (same "never re-derive a
    # historical grade" contract this endpoint already promises above).
    summary["feedback"] = crud.feedback_summary(
        crud.get_feedback_by_session(db, session.id)
    )
    summary["trend"] = _compute_trend(db, session, result)
    logger.info(
        "module-b result session=%s exercise=%s model=%s",
        session_id,
        exercise.code,
        result.model_version,
    )
    return ModuleBResultResponse(**summary)


def _fallback_reason_for_client_error(error: str | None) -> str:
    """Map `LlmRewriteResult.error` onto the stored `fallback_reason` vocabulary."""
    if error is None:
        return "api_error"  # defensive: text=None should always carry an error string
    if error == "http_429":
        return "rate_limited"
    if error == "timeout":
        return "timeout"
    if error == "invalid_json":
        return "invalid_json"
    if error == "empty_response":
        return "empty_response"
    return "api_error"  # other http_* statuses and transport_error:* messages


def _build_and_save_feedback(
    db: DbSession, *, session_id: UUID, summary: dict
) -> dict | None:
    """Stage 6.2/6.5/6.4: compose the deterministic template from the just-built result,
    optionally try a Groq rewrite on top (config-gated, after-set only -- this function is
    only reachable from `/analyze`, which runs once the whole set is already scored), and
    persist whichever text survives Stage 6.3's safety filter. Every analyzed set always
    gets a working report even if the LLM is disabled, times out, or is rejected.

    UAT remediation (Stage R3, T11, S5 "keeps showing template fallback"): the client
    and the safety filter both already computed a precise reason whenever a rewrite
    wasn't used, but it was only logged, never stored -- `fallback_reason` below is
    that reason made queryable per row instead of requiring a log-file search.
    """
    structured = build_structured_feedback(summary)
    # Stage 5.17: template_text is now the canonical `feedback_contract` JSON string,
    # the same shape an accepted LLM rewrite produces -- the report always renders one
    # thing regardless of which layer wrote it.
    template_text = serialize_feedback_contract(compose_template(structured))

    rewritten_text = template_text
    feedback_source = "template"
    llm_attempted = False
    provider: str | None = None
    model_version: str | None = None
    fallback_reason = "none"

    if settings.feedback_llm_enabled and settings.llm_api_key:
        llm_attempted = True
        # `llm_api_key`/`llm_model` are provider-agnostic naming; GroqClient is the one
        # adapter that reads them today (see core/config.py's comment).
        client = GroqClient(api_key=settings.llm_api_key, model=settings.llm_model)
        result = client.rewrite_feedback(structured=structured)
        provider = result.provider
        model_version = result.model_version
        if result.text is None:
            fallback_reason = _fallback_reason_for_client_error(result.error)
            logger.info(
                "module-b feedback llm_failed session=%s error=%s",
                session_id,
                result.error,
            )
        else:
            safety = check_llm_feedback(result.text, structured=structured)
            if safety.accepted:
                rewritten_text = result.text
                feedback_source = "llm"
                fallback_reason = "llm_used"
                logger.info(
                    "module-b feedback llm_used session=%s provider=%s model=%s",
                    session_id,
                    provider,
                    model_version,
                )
            else:
                fallback_reason = f"guard_rejected:{safety.reason}"
                logger.info(
                    "module-b feedback llm_rejected session=%s reason=%s",
                    session_id,
                    safety.reason,
                )
    else:
        logger.info("module-b feedback llm_disabled session=%s", session_id)

    row = crud.save_feedback(
        db,
        session_id=session_id,
        feedback=crud.FeedbackWrite(
            structured_feedback=template_text,
            rewritten_feedback=rewritten_text,
            feedback_source=feedback_source,
            llm_attempted=llm_attempted,
            provider=provider,
            model_version=model_version,
            disclaimer_version=CURRENT_DISCLAIMER_VERSION,
            fallback_reason=fallback_reason,
        ),
    )
    return crud.feedback_summary(row)


def _build_error_tags(
    exercise, fusion, gate_result, rule_scores
) -> list[crud.ErrorTagWrite]:
    """Prefer an exercise's own taxonomy-driven tag builder (Stage 6.1); fall back to the
    generic system+gate construction for any exercise that defines no builder."""
    tags = exercise.build_error_tags(
        fusion=fusion, gate_result=gate_result, rule_scores=rule_scores
    )
    if tags is not None:
        return tags
    return _system_error_tags(fusion.flags) + _fault_gate_tags(gate_result)


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
