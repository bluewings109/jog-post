from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivitiesPageResponse, ActivityDetailResponse, ActivityResponse

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
    """특정 활동의 상세 정보를 반환한다."""
    result = await db.execute(
        select(Activity).where(Activity.id == activity_id, Activity.user_id == current_user.id)
    )
    activity = result.scalar_one_or_none()

    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    return ActivityDetailResponse.model_validate(activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """활동을 로컬 DB에서 삭제한다 (Apple Health 원본은 유지)."""
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
