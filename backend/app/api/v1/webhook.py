"""Strava Webhook 엔드포인트.

GET  /webhook/strava — Strava 구독 검증 (hub.challenge)
POST /webhook/strava — 운동 이벤트 수신 → 200 즉시 응답 + BackgroundTask
"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.activity_sync import sync_activity_from_webhook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("/strava")
async def strava_verify(request: Request) -> JSONResponse:
    """Strava 구독 검증 요청에 응답한다.

    Strava가 구독 등록 시 한 번 호출한다:
      GET /webhook/strava?hub.mode=subscribe&hub.challenge=XXX&hub.verify_token=YYY
    """
    params = request.query_params
    if params.get("hub.verify_token") != settings.STRAVA_WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verify_token")

    return JSONResponse({"hub.challenge": params.get("hub.challenge", "")})


@router.post("/strava", status_code=status.HTTP_200_OK)
async def strava_event(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Strava 활동 이벤트를 수신한다.

    Strava는 3초 내 응답을 요구하므로 즉시 200을 반환하고,
    실제 처리는 BackgroundTask에서 수행한다.

    처리 대상 이벤트:
      - object_type == "activity"
      - aspect_type == "create"
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    if body.get("object_type") == "activity" and body.get("aspect_type") == "create":
        activity_id = body.get("object_id")
        athlete_id = body.get("owner_id")
        if activity_id and athlete_id:
            background_tasks.add_task(_process_activity, int(activity_id), int(athlete_id))

    return {"status": "ok"}


async def _process_activity(strava_activity_id: int, strava_athlete_id: int) -> None:
    """BackgroundTask: 새 DB 세션을 열어 활동을 동기화한다."""
    async with AsyncSessionLocal() as db:
        try:
            activity = await sync_activity_from_webhook(
                strava_activity_id, strava_athlete_id, db
            )
            if activity:
                logger.info(
                    "Synced activity strava_id=%s user_id=%s",
                    strava_activity_id,
                    activity.user_id,
                )
        except Exception:
            logger.exception(
                "Unexpected error syncing activity strava_id=%s", strava_activity_id
            )
