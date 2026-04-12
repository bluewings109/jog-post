from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Lap(Base):
    __tablename__ = "laps"

    id: Mapped[int] = mapped_column(primary_key=True)
    strava_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    lap_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    elapsed_time: Mapped[int | None] = mapped_column(Integer)       # 초
    moving_time: Mapped[int | None] = mapped_column(Integer)        # 초
    distance: Mapped[float | None] = mapped_column(Float)           # 미터
    average_speed: Mapped[float | None] = mapped_column(Float)
    max_speed: Mapped[float | None] = mapped_column(Float)
    average_cadence: Mapped[float | None] = mapped_column(Float)
    average_heartrate: Mapped[float | None] = mapped_column(Float)
    max_heartrate: Mapped[float | None] = mapped_column(Float)
    total_elevation_gain: Mapped[float | None] = mapped_column(Float)
    pace_zone: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    activity: Mapped["Activity"] = relationship(back_populates="laps")

    __table_args__ = (Index("idx_laps_activity_id", "activity_id"),)
