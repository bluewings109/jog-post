from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# 지원 공급자 타입 — 향후 다른 웹훅 기반 소스 추가 가능
ProviderType = Literal["apple_health"]


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
    provider: Mapped[str] = mapped_column(String(50), nullable=False)   # "apple_health" | ...
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)  # 공급자 측 식별자
    webhook_secret: Mapped[str | None] = mapped_column(String(100), unique=True)  # 웹훅 인증용 시크릿
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="data_sources")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_data_sources_user_provider"),
        Index("idx_data_sources_user_id", "user_id"),
    )
