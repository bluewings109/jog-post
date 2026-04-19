from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivitiesPageResponse, ActivityDetailResponse, ActivityResponse
from app.services import strava_auth
from app.services.activity_sync import sync_activities_bulk

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=ActivitiesPageResponse)
async def list_activities(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivitiesPageResponse:
    """사용자의 달리기 활동 목록을 최신순으로 반환한다."""
    base = select(Activity).where(Activity.user_id == current_user.id)

    if start_date:
        base = base.where(Activity.start_date >= start_date)
    if end_date:
        base = base.where(Activity.start_date <= end_date)

    total = await db.scalar(select(func.count()).select_from(base.subquery()))

    result = await db.execute(
        base.order_by(Activity.start_date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    activities = result.scalars().all()

    return ActivitiesPageResponse(
        items=[ActivityResponse.model_validate(a) for a in activities],
        total=total or 0,
        page=page,
        per_page=per_page,
    )


@router.get("/{activity_id}", response_model=ActivityDetailResponse)
async def get_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivityDetailResponse:
    """특정 활동의 상세 정보와 랩 목록을 반환한다."""
    result = await db.execute(
        select(Activity)
        .where(Activity.id == activity_id, Activity.user_id == current_user.id)
        .options(selectinload(Activity.laps))
    )
    activity = result.scalar_one_or_none()

    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    return ActivityDetailResponse.model_validate(activity)


@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Strava에서 과거 달리기 활동을 수동으로 동기화한다.

    Strava Rate Limit(15분당 200회)으로 인해 최대 300개(10페이지)까지 처리한다.
    """
    data_source = await strava_auth.get_strava_data_source(current_user.id, db)
    if data_source is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strava 연동이 필요합니다. /auth/strava/connect 를 먼저 완료하세요.",
        )

    try:
        saved = await sync_activities_bulk(int(data_source.external_id), db)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Strava API 요청 한도를 초과했습니다. 15분 후 다시 시도해주세요.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Strava API 오류가 발생했습니다.",
        )
    return {"synced": saved}


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """활동을 로컬 DB에서 삭제한다 (Strava 원본은 유지)."""
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id,
            Activity.user_id == current_user.id,
        )
    )
    activity = result.scalar_one_or_none()

    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    await db.delete(activity)
    await db.commit()
