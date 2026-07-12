"""Apple Health(Health Auto Export) Webhook 엔드포인트.

POST /webhook/apple-health — 운동 데이터 수신 (X-Webhook-Secret 헤더로 사용자 식별)
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import apple_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/apple-health", status_code=status.HTTP_200_OK)
async def apple_health_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Health Auto Export 앱이 보내는 운동 데이터를 수신한다.

    Health Auto Export는 Strava와 달리 응답 시간 제약이 없으므로 동기적으로 처리한다.
    같은 운동이 재전송될 수 있어 apple_health_id 기준으로 멱등하게 upsert한다.
    """
    if not x_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Webhook-Secret")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    data_source = await apple_health.get_data_source_by_webhook_secret(x_webhook_secret, db)
    if data_source is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    result = await apple_health.sync_workouts(body, data_source.user_id, db)
    logger.info(
        "Apple Health sync: user_id=%s saved=%s skipped=%s",
        data_source.user_id,
        result["saved"],
        result["skipped"],
    )
    return result
