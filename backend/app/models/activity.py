from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL에서는 JSONB, SQLite(테스트)에서는 JSON으로 자동 전환
_JsonType = JSON().with_variant(JSONB(), "postgresql")

from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    strava_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(50))
    sport_type: Mapped[str | None] = mapped_column(String(50))
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_date_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str | None] = mapped_column(String(100))

    distance: Mapped[float | None] = mapped_column(Float)           # 미터
    moving_time: Mapped[int | None] = mapped_column(Integer)        # 초
    elapsed_time: Mapped[int | None] = mapped_column(Integer)       # 초
    total_elevation_gain: Mapped[float | None] = mapped_column(Float)
    average_speed: Mapped[float | None] = mapped_column(Float)      # m/s
    max_speed: Mapped[float | None] = mapped_column(Float)
    average_cadence: Mapped[float | None] = mapped_column(Float)
    average_heartrate: Mapped[float | None] = mapped_column(Float)
    max_heartrate: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    suffer_score: Mapped[int | None] = mapped_column(Integer)

    summary_polyline: Mapped[str | None] = mapped_column(Text)
    map_id: Mapped[str | None] = mapped_column(String(100))

    achievement_count: Mapped[int] = mapped_column(Integer, default=0)
    kudos_count: Mapped[int] = mapped_column(Integer, default=0)
    pr_count: Mapped[int] = mapped_column(Integer, default=0)

    trainer: Mapped[bool] = mapped_column(Boolean, default=False)
    commute: Mapped[bool] = mapped_column(Boolean, default=False)
    manual: Mapped[bool] = mapped_column(Boolean, default=False)

    raw_json: Mapped[dict | None] = mapped_column(_JsonType)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="activities")
    laps: Mapped[list["Lap"]] = relationship(back_populates="activity", cascade="all, delete-orphan")
    llm_advices: Mapped[list["LLMAdvice"]] = relationship(back_populates="activity")

    __table_args__ = (
        Index("idx_activities_user_id", "user_id"),
        Index("idx_activities_start_date", "start_date"),
    )
