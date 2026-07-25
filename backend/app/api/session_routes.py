import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ExerciseCatalog
from app.db.models import Session as SessionModel
from app.db.models import User
from app.db.schemas import SessionEnd, SessionRead, SessionStart, SessionStartResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


def _decimal_to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _session_response(session: SessionModel) -> SessionRead:
    return SessionRead(
        id=session.id,
        mode=session.mode,
        exercise_code=session.exercise.code,
        exercise_name=session.exercise.name,
        exercise_type=session.exercise_type,
        started_at=session.started_at,
        ended_at=session.ended_at,
        status=session.status,
        capture_quality=_decimal_to_float(session.capture_quality),
        valid_frame_ratio=_decimal_to_float(session.valid_frame_ratio),
        score=_decimal_to_float(session.score),
        band=session.band,
        rep_count=session.rep_count,
        target_rep_count=session.target_rep_count,
    )


def _get_owned_session(
    db: DbSession, session_id: UUID, user_id: UUID
) -> SessionModel | None:
    return db.scalar(
        select(SessionModel)
        .options(selectinload(SessionModel.exercise))
        .where(SessionModel.id == session_id, SessionModel.user_id == user_id)
    )


def _require_in_progress(session: SessionModel, action: str) -> None:
    """Keep a finished or cancelled session from being changed later."""
    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only an in-progress session can be {action}.",
        )


@router.post(
    "/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED
)
def start_session(
    payload: SessionStart,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionStartResponse:
    exercise = db.scalar(
        select(ExerciseCatalog).where(ExerciseCatalog.code == payload.exercise_code)
    )
    if exercise is None or not exercise.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )

    # A user can only have one active browser session. This also cleans up a
    # previous session if its browser closed before its page-exit request arrived.
    abandoned_sessions = db.scalars(
        select(SessionModel).where(
            SessionModel.user_id == current_user.id,
            SessionModel.status == "in_progress",
        )
    ).all()
    now = datetime.now(UTC)
    for abandoned_session in abandoned_sessions:
        abandoned_session.ended_at = now
        abandoned_session.status = "cancelled"

    if abandoned_sessions:
        logger.info(
            "cancelled abandoned sessions user=%s count=%d",
            current_user.id,
            len(abandoned_sessions),
        )

    session = SessionModel(
        user_id=current_user.id,
        exercise_id=exercise.id,
        mode=payload.mode,
        exercise_type=exercise.code,
        started_at=now,
        status="in_progress",
        device_info=payload.device_info,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionStartResponse(session_id=session.id, status=session.status)


@router.post("/{session_id}/end", response_model=SessionRead)
def end_session(
    session_id: UUID,
    payload: SessionEnd,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionRead:
    session = _get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    _require_in_progress(session, "ended")

    session.ended_at = datetime.now(UTC)
    session.status = "completed"
    session.capture_quality = payload.capture_quality
    session.valid_frame_ratio = payload.valid_frame_ratio
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(session)


@router.post("/{session_id}/cancel", response_model=SessionRead)
def cancel_session(
    session_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionRead:
    """Marks a session as cancelled — never scored, never shown as completed."""
    session = _get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # A second close-page/cancel request is harmless, but a completed session
    # must never be overwritten as cancelled.
    if session.status == "cancelled":
        return _session_response(session)
    _require_in_progress(session, "cancelled")

    session.ended_at = datetime.now(UTC)
    session.status = "cancelled"
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(session)


@router.get("", response_model=list[SessionRead])
def list_sessions(
    db: DbSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[SessionRead]:
    sessions = db.scalars(
        select(SessionModel)
        .options(selectinload(SessionModel.exercise))
        .where(SessionModel.user_id == current_user.id)
        .order_by(SessionModel.started_at.desc())
    )
    return [_session_response(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionRead)
def get_session(
    session_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionRead:
    session = _get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return _session_response(session)
