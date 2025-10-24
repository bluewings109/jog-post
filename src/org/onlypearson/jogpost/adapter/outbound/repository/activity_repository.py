import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from org.onlypearson.jogpost.adapter.outbound.repository.orm.activity import Activity
from org.onlypearson.jogpost.domain.model.activity_domain import ActivityDomain
from org.onlypearson.jogpost.exception.custom_exception import StravaException
from org.onlypearson.jogpost.exception.error_code import ErrorCode


class ActivityRepository:
    async def select_by_id_with_no_raise(self, activity_id: int, session: AsyncSession) -> ActivityDomain | None:
        activity: Activity|None = await session.get(Activity, activity_id)

        if activity is None:
            return None

        return activity.to_domain()

    async def update_is_posted(
        self,
        activity_id: int,
        is_posted: bool,
        session: AsyncSession
    ):
        activity: Activity | None = await session.get(Activity, activity_id)

        if activity is None:
            raise StravaException(ErrorCode.STRAVA_ACTIVITY_ERROR_3.value)

        activity.is_posted = is_posted
        activity.post_date = datetime.datetime.now(datetime.UTC)

    async def insert_activity(self, activity_domain: ActivityDomain, session: AsyncSession) -> ActivityDomain:
        activity: Activity = Activity.from_domain(activity_domain)
        session.add(activity)
        return activity.to_domain()
