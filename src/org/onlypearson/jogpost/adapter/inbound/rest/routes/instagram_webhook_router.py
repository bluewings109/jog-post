from typing import Annotated

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Query
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from org.onlypearson.jogpost.application.services.instagram_service import InstagramService
from org.onlypearson.jogpost.database.session import get_session
from org.onlypearson.jogpost.di_container import Container

router = APIRouter(prefix="/api/instagram/webhook")

@router.get("/verify")
@inject
async def verify_token(
    code: Annotated[str, Query()],
    instagram_service: Annotated[InstagramService, Depends(Provide[Container.instagram_service])],
    session:Annotated[AsyncSession, Depends(get_session)],
    error: Annotated[str|None, Query()]=None,
    error_reason: Annotated[str|None, Query()]=None,
    error_description: Annotated[str|None, Query()]=None,
    athlete_id_in_str: Annotated[str|None, Query(alias="state")]=None,

):
    if error is not None:
        return {
            "error": error,
            "error_reason": error_reason,
            "error_description": error_description,
        }

    print(f"athlete_id_in_str={athlete_id_in_str}, type(athlete_id_in_str={type(athlete_id_in_str)}")
    await instagram_service.initial_verify(int(athlete_id_in_str), "https://localhost:7070/api/instagram/webhook/verify", code, session)
    return {"status": "ok"}



