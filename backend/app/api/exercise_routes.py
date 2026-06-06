from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ExerciseCatalog, User
from app.db.schemas import ExerciseRead

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseRead])
def list_exercises(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[ExerciseCatalog]:
    return list(
        db.scalars(
            select(ExerciseCatalog)
            .where(ExerciseCatalog.is_active.is_(True))
            .order_by(ExerciseCatalog.mode, ExerciseCatalog.name)
        )
    )


@router.get("/{exercise_code}", response_model=ExerciseRead)
def get_exercise(
    exercise_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ExerciseCatalog:
    exercise = db.scalar(
        select(ExerciseCatalog).where(ExerciseCatalog.code == exercise_code)
    )
    if exercise is None or not exercise.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )
    return exercise
