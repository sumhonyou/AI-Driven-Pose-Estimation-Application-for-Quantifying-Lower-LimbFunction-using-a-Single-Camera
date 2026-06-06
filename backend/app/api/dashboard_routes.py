from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.session_routes import _session_response
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.db.schemas import DashboardErrorTag, DashboardSummary, DashboardTrendPoint

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: DbSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DashboardSummary:
    total_sessions = db.scalar(
        select(func.count(SessionModel.id)).where(SessionModel.user_id == current_user.id)
    )
    avg_capture_quality = db.scalar(
        select(func.avg(SessionModel.capture_quality)).where(
            SessionModel.user_id == current_user.id,
            SessionModel.capture_quality.is_not(None),
        )
    )
    recent_sessions = list(
        db.scalars(
            select(SessionModel)
            .options(selectinload(SessionModel.exercise))
            .where(SessionModel.user_id == current_user.id)
            .order_by(SessionModel.started_at.desc())
            .limit(5)
        )
    )

    return DashboardSummary(
        total_sessions=total_sessions or 0,
        avg_capture_quality=float(avg_capture_quality)
        if avg_capture_quality is not None
        else None,
        latest_score=None,
        latest_band=None,
        recent_sessions=[_session_response(session) for session in recent_sessions],
    )


@router.get("/trends", response_model=list[DashboardTrendPoint])
def get_trends(_: User = Depends(get_current_user)) -> list[DashboardTrendPoint]:
    return []


@router.get("/error-tags", response_model=list[DashboardErrorTag])
def get_error_tags(_: User = Depends(get_current_user)) -> list[DashboardErrorTag]:
    return []
