from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

import datetime

from org.onlypearson.jogpost.adapter.outbound.repository.orm.base_table import AbstractBaseTable
from org.onlypearson.jogpost.domain.model.activity_domain import ActivityDomain

class Activity(AbstractBaseTable):
    __tablename__ = "activity"

    athlete_id: Mapped[int|None] = mapped_column(BigInteger, index=True)
    name: Mapped[str|None] = mapped_column(String)
    distance: Mapped[float|None] = mapped_column(Float)
    elapsed_time: Mapped[float|None] = mapped_column(Float)
    type: Mapped[str|None] = mapped_column(String)
    start_date: Mapped[datetime.datetime|None] = mapped_column(DateTime(timezone=True), index=True)
    average_heartrate: Mapped[float|None] = mapped_column(Float)
    max_heartrate: Mapped[float|None] = mapped_column(Float)
    polyline: Mapped[str|None] = mapped_column(String)
    summary_polyline: Mapped[str|None] = mapped_column(String)
    post_date: Mapped[datetime.datetime|None] = mapped_column(DateTime(timezone=True))
    is_posted: Mapped[bool|None] = mapped_column(Boolean)

    def to_domain(self) -> ActivityDomain:
        return ActivityDomain(
            activity_id=self.id,
            athlete_id=self.athlete_id,
            name=self.name,
            distance=self.distance,
            elapsed_time=self.elapsed_time,
            type=self.type,
            start_date=self.start_date,
            average_heartrate=self.average_heartrate,
            max_heartrate=self.max_heartrate,
            polyline=self.polyline,
            summary_polyline=self.summary_polyline,
            post_date=self.post_date,
            is_posted=self.is_posted,
        )

    @staticmethod
    def from_domain(activity_domain: ActivityDomain):
        return Activity(
            id=activity_domain.activity_id,
            athlete_id=activity_domain.athlete_id,
            name=activity_domain.name,
            distance=activity_domain.distance,
            elapsed_time=activity_domain.elapsed_time,
            type=activity_domain.type,
            start_date=activity_domain.start_date,
            average_heartrate=activity_domain.average_heartrate,
            max_heartrate=activity_domain.max_heartrate,
            polyline=activity_domain.polyline,
            summary_polyline=activity_domain.summary_polyline,
            post_date=activity_domain.post_date,
            is_posted=activity_domain.is_posted,
        )
