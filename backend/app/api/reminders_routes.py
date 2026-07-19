"""Stage 7.3: reminders CRUD + calendar export.

No email, no push, no background scheduler -- delivery is a Google Calendar link
and a downloadable .ics file, both computed on read so they always reflect the
reminder's current title/time/frequency (never go stale like a persisted copy
would). See app/api/reminders_service.py for the pure due-ness/calendar logic.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api import reminders_service as svc
from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ExerciseCatalog, Reminder, User
from app.db.schemas import ReminderCreate, ReminderResponse, ReminderUpdate

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


def _get_owned_reminder(db: DbSession, reminder_id: UUID, user_id: UUID) -> Reminder:
    reminder = db.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
    )
    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )
    return reminder


def _exercise_catalog(db: DbSession) -> dict[str, ExerciseCatalog]:
    """Small table (one row per exercise variant) -- fetched whole and reused
    across every reminder in a response rather than one query per row."""
    return {e.code: e for e in db.scalars(select(ExerciseCatalog))}


def _to_response(
    reminder: Reminder, exercises: dict[str, ExerciseCatalog], now: datetime
) -> ReminderResponse:
    exercise = exercises.get(reminder.exercise_code) if reminder.exercise_code else None
    return ReminderResponse(
        id=reminder.id,
        title=reminder.title,
        reminder_time=reminder.reminder_time,
        frequency=reminder.frequency,
        is_active=reminder.is_active,
        exercise_code=reminder.exercise_code,
        last_completed_at=reminder.last_completed_at,
        created_at=reminder.created_at,
        is_due=svc.is_due(reminder, now),
        # Only surfaced when the linked exercise is still active -- the frontend
        # gates the deep-link on this being present rather than trusting a
        # possibly-retired exercise_code (e.g. the removed Lunge exercise).
        exercise_name=exercise.name if exercise and exercise.is_active else None,
        exercise_mode=exercise.mode if exercise and exercise.is_active else None,
        google_calendar_url=svc.build_google_calendar_url(reminder),
        ics_url=f"/api/reminders/{reminder.id}/export.ics",
    )


@router.get("", response_model=list[ReminderResponse])
def list_reminders(
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReminderResponse]:
    reminders = list(
        db.scalars(
            select(Reminder)
            .where(Reminder.user_id == current_user.id)
            .order_by(Reminder.reminder_time)
        )
    )
    exercises = _exercise_catalog(db)
    now = datetime.now(UTC)
    return [_to_response(r, exercises, now) for r in reminders]


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderResponse:
    reminder = Reminder(
        user_id=current_user.id,
        title=payload.title,
        reminder_time=payload.reminder_time,
        frequency=payload.frequency,
        exercise_code=payload.exercise_code,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return _to_response(reminder, _exercise_catalog(db), datetime.now(UTC))


@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: UUID,
    payload: ReminderUpdate,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderResponse:
    reminder = _get_owned_reminder(db, reminder_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(reminder, field, value)
    db.commit()
    db.refresh(reminder)
    return _to_response(reminder, _exercise_catalog(db), datetime.now(UTC))


@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
def complete_reminder(
    reminder_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderResponse:
    reminder = _get_owned_reminder(db, reminder_id, current_user.id)
    reminder.last_completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(reminder)
    return _to_response(reminder, _exercise_catalog(db), datetime.now(UTC))


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    reminder = _get_owned_reminder(db, reminder_id, current_user.id)
    db.delete(reminder)
    db.commit()


@router.get("/{reminder_id}/export.ics")
def export_reminder_ics(
    reminder_id: UUID,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    reminder = _get_owned_reminder(db, reminder_id, current_user.id)
    ics_text = svc.build_ics(reminder)
    return Response(
        content=ics_text,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="reminder-{reminder.id}.ics"'
        },
    )
