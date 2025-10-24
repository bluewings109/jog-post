import asyncio
from typing import Annotated

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from org.onlypearson.jogpost.application.services.strava_service import StravaService
from org.onlypearson.jogpost.database.session import get_session
from org.onlypearson.jogpost.di_container import Container
from org.onlypearson.jogpost.schema.strava_api_dto import StravaWebhookRequest

router = APIRouter(prefix="/api/webhook")

@router.get("")
async def verify_token(
    hub_verify_token: Annotated[str, Query(alias="hub.verify_token")],
    hub_challenge: Annotated[str, Query(alias="hub.challenge")],
    hub_mode: Annotated[str, Query(alias="hub.mode")],
):
    if hub_verify_token == "JOG-POST-STRAVA":
        return {"hub.challenge": hub_challenge}

    elif hub_verify_token == "JOG-POST-INSTAGRAM":
        return {"hub.challenge": hub_challenge}

    return {"error": "Unauthorized"}

@router.post("")
@inject
async def push_event(
    request: StravaWebhookRequest,
    strava_service: Annotated[StravaService, Depends(Provide[Container.strava_service])],
):
    asyncio.create_task(strava_service.process_webhook_event(request))
    return {"status": "ok"}


@router.post("/token")
@inject
async def get_access_token(
    strava_service: Annotated[StravaService, Depends(Provide[Container.strava_service])],
    session:Annotated[AsyncSession, Depends(get_session)],
):
    strava_token = await strava_service.ensure_access_token(104634892, session)
    return {"access_token": strava_token}

@router.post("/test")
@inject
async def test(
    activity_id: Annotated[int, Query()],
    strava_service: Annotated[StravaService, Depends(Provide[Container.strava_service])],
    session:Annotated[AsyncSession, Depends(get_session)],
):
    await strava_service.process_activity_event(activity_id, 104634892, session, is_test=False)
    return "OK"

@router.get("/test")
async def test2():
    return "OK"
