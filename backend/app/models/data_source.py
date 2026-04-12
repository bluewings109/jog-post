from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# 지원 공급자 타입 — 향후 "apple", "samsung" 등 추가
ProviderType = Literal["strava"]


class DataSource(Base):
    """사용자별 외부 운동 데이터 공급자 연동 정보.

    한 사용자가 여러 공급자를 연동할 수 있으며,
    공급자당 하나의 연동만 허용한다 (user_id + provider UNIQUE).
    """

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)   # "strava" | ...
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)  # 공급자 측 사용자 ID
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str | None] = mapped_column(Text)                    # 승인된 scope 문자열
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="data_sources")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_data_sources_user_provider"),
        Index("idx_data_sources_user_id", "user_id"),
    )
