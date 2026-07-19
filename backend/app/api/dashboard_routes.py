from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import selectinload

from app.api.dashboard_service import build_error_tags, build_latest, build_trends
from app.api.deps import get_current_user
from app.api.session_routes import _session_response
from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.db.models import User
from app.db.schemas import DashboardErrorTag, DashboardSummary, ExerciseTrend

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _apply_range(stmt, from_: datetime | None, to: datetime | None):
    # Optional inclusive date window on session start time.
    if from_ is not None:
        stmt = stmt.where(SessionModel.started_at >= from_)
    if to is not None:
        stmt = stmt.where(SessionModel.started_at <= to)
    return stmt


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: DbSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DashboardSummary:
    total_sessions = db.scalar(
        select(func.count(SessionModel.id)).where(
            SessionModel.user_id == current_user.id
        )
    )
    avg_capture_quality = db.scalar(
        select(func.avg(SessionModel.capture_quality)).where(
            SessionModel.user_id == current_user.id,
            SessionModel.capture_quality.is_not(None),
        )
    )
    # All sessions newest-first: first 5 feed the "recent" table, and the full
    # list feeds the per-exercise "latest" map (latest may be older than top 5).
    all_sessions = list(
        db.scalars(
            select(SessionModel)
            .options(selectinload(SessionModel.exercise))
            .where(SessionModel.user_id == current_user.id)
            .order_by(SessionModel.started_at.desc())
        )
    )
    recent_sessions = all_sessions[:5]
    latest_scored = next((s for s in recent_sessions if s.score is not None), None)

    return DashboardSummary(
        total_sessions=total_sessions or 0,
        avg_capture_quality=(
            float(avg_capture_quality) if avg_capture_quality is not None else None
        ),
        latest_score=float(latest_scored.score) if latest_scored else None,
        latest_band=latest_scored.band if latest_scored else None,
        recent_sessions=[_session_response(session) for session in recent_sessions],
        latest=build_latest(all_sessions),
    )


@router.get("/trends", response_model=dict[str, ExerciseTrend])
def get_trends(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None, alias="to"),
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, ExerciseTrend]:
    # Oldest-first so each exercise's series reads left-to-right on the chart.
    stmt = (
        select(SessionModel)
        .options(selectinload(SessionModel.module_b_result))
        .where(SessionModel.user_id == current_user.id)
        .order_by(SessionModel.started_at.asc())
    )
    sessions = list(db.scalars(_apply_range(stmt, from_, to)))
    return build_trends(sessions)


@router.get("/error-tags", response_model=dict[str, list[DashboardErrorTag]])
def get_error_tags(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None, alias="to"),
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[DashboardErrorTag]]:
    stmt = (
        select(SessionModel)
        .options(
            selectinload(SessionModel.module_b_result),
            selectinload(SessionModel.module_b_error_tags),
        )
        .where(SessionModel.user_id == current_user.id)
    )
    sessions = list(db.scalars(_apply_range(stmt, from_, to)))
    return build_error_tags(sessions)
