from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from org.onlypearson.jogpost.adapter.outbound.repository.orm.athlete import Athlete

from org.onlypearson.jogpost.domain.model.athlete_domain import AthleteDomain
from org.onlypearson.jogpost.exception.error_code import ErrorCode
from org.onlypearson.jogpost.exception.custom_exception import StravaException


class AthleteRepository:
    async def select_by_id(self, athlete_id: int, session: AsyncSession) -> AthleteDomain:
        stmt = select(Athlete).where(Athlete.id == athlete_id)
        result = await session.execute(stmt)
        selected_row: Athlete | None = result.scalar_one_or_none()

        if selected_row is None:
            raise StravaException(ErrorCode.STRAVA_ATHLETE_ERROR_1.value)

        return selected_row.to_domain()

    async def update_athlete_token(
        self,
        athlete_id: int,
        access_token: str,
        refresh_token: str,
        expire_date: int,
        session: AsyncSession
    ):
        stmt = update(Athlete).where(Athlete.id == athlete_id).values(access_token=access_token, refresh_token=refresh_token, expire_date=expire_date)
        await session.execute(stmt)

    async def update_instagram_token(
        self,
        athlete_id: int,
        instagram_access_token: str,
        instagram_expire_date: int,
        session: AsyncSession
    ):
        stmt = update(Athlete).where(Athlete.id == athlete_id).values(instagram_access_token=instagram_access_token, instagram_expire_date=instagram_expire_date)
        await session.execute(stmt)
