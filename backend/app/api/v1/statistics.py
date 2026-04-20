import calendar
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.schemas.statistics import (
    MonthlyStatsResponse,
    PeriodStatsItem,
    WeeklyStatsResponse,
    YearlyStatsResponse,
)

router = APIRouter(prefix="/statistics", tags=["statistics"])

_MONTH_LABELS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]


def _build_item(
    period_label: str,
    period_start: datetime,
    activity_count: int,
    total_distance_m: float | None,
    total_moving_time: int | None,
    avg_heartrate: float | None,
    total_elevation_gain: float | None,
) -> PeriodStatsItem:
    total_dist_km = (total_distance_m or 0) / 1000
    moving_time = int(total_moving_time or 0)
    avg_pace = (moving_time / total_dist_km) if total_dist_km > 0 else None

    return PeriodStatsItem(
        period_label=period_label,
        period_start=period_start,
        activity_count=activity_count,
        total_distance=round(total_dist_km, 2),
        total_moving_time=moving_time,
        avg_pace_sec_per_km=round(avg_pace, 1) if avg_pace is not None else None,
        avg_heartrate=round(float(avg_heartrate), 1) if avg_heartrate else None,
        total_elevation_gain=round(float(total_elevation_gain or 0), 1),
    )


@router.get("/weekly", response_model=WeeklyStatsResponse)
async def get_weekly_stats(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyStatsResponse:
    """특정 월의 주별 집계 통계를 반환한다."""
    last_day = calendar.monthrange(year, month)[1]
    range_start = datetime(year, month, 1)
    range_end = datetime(year, month, last_day, 23, 59, 59)

    stmt = (
        select(
            func.date_trunc("week", Activity.start_date_local).label("week_start"),
            func.count(Activity.id).label("activity_count"),
            func.sum(Activity.distance).label("total_distance_m"),
            func.sum(Activity.moving_time).label("total_moving_time"),
            func.avg(Activity.average_heartrate).label("avg_heartrate"),
            func.sum(Activity.total_elevation_gain).label("total_elevation_gain"),
        )
        .where(
            Activity.user_id == current_user.id,
            Activity.start_date_local >= range_start,
            Activity.start_date_local <= range_end,
        )
        .group_by(func.date_trunc("week", Activity.start_date_local))
        .order_by(func.date_trunc("week", Activity.start_date_local))
    )

    result = await db.execute(stmt)
    rows = result.all()

    weeks = []
    for row in rows:
        week_start: datetime = row.week_start
        week_num = week_start.isocalendar()[1]
        label = f"{week_start.year}년 {week_num}주차"
        weeks.append(
            _build_item(
                label,
                week_start,
                int(row.activity_count),
                row.total_distance_m,
                row.total_moving_time,
                row.avg_heartrate,
                row.total_elevation_gain,
            )
        )

    return WeeklyStatsResponse(year=year, month=month, weeks=weeks)


@router.get("/monthly", response_model=MonthlyStatsResponse)
async def get_monthly_stats(
    year: int = Query(..., ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MonthlyStatsResponse:
    """특정 연도의 월별 집계 통계를 반환한다."""
    range_start = datetime(year, 1, 1)
    range_end = datetime(year, 12, 31, 23, 59, 59)

    stmt = (
        select(
            func.date_trunc("month", Activity.start_date_local).label("month_start"),
            func.count(Activity.id).label("activity_count"),
            func.sum(Activity.distance).label("total_distance_m"),
            func.sum(Activity.moving_time).label("total_moving_time"),
            func.avg(Activity.average_heartrate).label("avg_heartrate"),
            func.sum(Activity.total_elevation_gain).label("total_elevation_gain"),
        )
        .where(
            Activity.user_id == current_user.id,
            Activity.start_date_local >= range_start,
            Activity.start_date_local <= range_end,
        )
        .group_by(func.date_trunc("month", Activity.start_date_local))
        .order_by(func.date_trunc("month", Activity.start_date_local))
    )

    result = await db.execute(stmt)
    rows = result.all()

    months = []
    for row in rows:
        month_start: datetime = row.month_start
        label = _MONTH_LABELS[month_start.month - 1]
        months.append(
            _build_item(
                label,
                month_start,
                int(row.activity_count),
                row.total_distance_m,
                row.total_moving_time,
                row.avg_heartrate,
                row.total_elevation_gain,
            )
        )

    return MonthlyStatsResponse(year=year, months=months)


@router.get("/yearly", response_model=YearlyStatsResponse)
async def get_yearly_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> YearlyStatsResponse:
    """전체 연도별 집계 통계를 반환한다."""
    stmt = (
        select(
            func.date_trunc("year", Activity.start_date_local).label("year_start"),
            func.count(Activity.id).label("activity_count"),
            func.sum(Activity.distance).label("total_distance_m"),
            func.sum(Activity.moving_time).label("total_moving_time"),
            func.avg(Activity.average_heartrate).label("avg_heartrate"),
            func.sum(Activity.total_elevation_gain).label("total_elevation_gain"),
        )
        .where(Activity.user_id == current_user.id)
        .group_by(func.date_trunc("year", Activity.start_date_local))
        .order_by(func.date_trunc("year", Activity.start_date_local))
    )

    result = await db.execute(stmt)
    rows = result.all()

    years = []
    for row in rows:
        year_start: datetime = row.year_start
        label = f"{year_start.year}년"
        years.append(
            _build_item(
                label,
                year_start,
                int(row.activity_count),
                row.total_distance_m,
                row.total_moving_time,
                row.avg_heartrate,
                row.total_elevation_gain,
            )
        )

    return YearlyStatsResponse(years=years)
