"""인증 없이 접근 가능한 공개 통계 엔드포인트.

사용자가 is_public=True 로 설정한 경우에만 데이터를 반환한다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.statistics import (
    _MONTHLY_SQL,
    _YEARLY_SQL,
    _MONTH_LABELS,
    _build_item,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.statistics import MonthlyStatsResponse, YearlyStatsResponse
from app.schemas.user import PublicUserResponse
from datetime import datetime

router = APIRouter(prefix="/public", tags=["public"])


async def _get_public_user(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users/{user_id}", response_model=PublicUserResponse)
async def get_public_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> PublicUserResponse:
    """user_id로 공개 사용자 정보를 조회한다. is_public=False 이면 404를 반환한다."""
    user = await _get_public_user(user_id, db)
    return PublicUserResponse(id=user.id, name=user.name, picture=user.picture)


@router.get("/users/lookup", response_model=PublicUserResponse)
async def lookup_public_user(
    email: str = Query(..., description="조회할 사용자 이메일"),
    db: AsyncSession = Depends(get_db),
) -> PublicUserResponse:
    """이메일로 공개 사용자를 조회한다. is_public=False 이면 404를 반환한다."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return PublicUserResponse(id=user.id, name=user.name, picture=user.picture)


@router.get("/users/{user_id}/statistics/yearly", response_model=YearlyStatsResponse)
async def get_public_yearly_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> YearlyStatsResponse:
    """공개 사용자의 연도별 통계를 반환한다."""
    user = await _get_public_user(user_id, db)

    result = await db.execute(_YEARLY_SQL, {"user_id": user.id})
    rows = result.mappings().all()

    years = []
    for row in rows:
        period_start: datetime = row["period_start"]
        label = f"{period_start.year}년"
        years.append(
            _build_item(
                label,
                period_start,
                int(row["activity_count"]),
                row["total_distance_m"],
                row["total_moving_time"],
                row["avg_heartrate"],
                row["total_elevation_gain"],
            )
        )

    return YearlyStatsResponse(years=years)


@router.get("/users/{user_id}/statistics/monthly", response_model=MonthlyStatsResponse)
async def get_public_monthly_stats(
    user_id: int,
    year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
) -> MonthlyStatsResponse:
    """공개 사용자의 특정 연도 월별 통계를 반환한다."""
    user = await _get_public_user(user_id, db)

    range_start = datetime(year, 1, 1)
    range_end = datetime(year, 12, 31, 23, 59, 59)

    result = await db.execute(
        _MONTHLY_SQL,
        {"user_id": user.id, "range_start": range_start, "range_end": range_end},
    )
    rows = result.mappings().all()

    months = []
    for row in rows:
        period_start: datetime = row["period_start"]
        label = _MONTH_LABELS[period_start.month - 1]
        months.append(
            _build_item(
                label,
                period_start,
                int(row["activity_count"]),
                row["total_distance_m"],
                row["total_moving_time"],
                row["avg_heartrate"],
                row["total_elevation_gain"],
            )
        )

    return MonthlyStatsResponse(year=year, months=months)
