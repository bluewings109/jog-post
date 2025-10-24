from sqlalchemy import BigInteger
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from org.onlypearson.jogpost.adapter.outbound.repository.orm.base_table import AbstractBaseTable
from org.onlypearson.jogpost.domain.model.athlete_domain import AthleteDomain


class Athlete(AbstractBaseTable):
    __tablename__ = "athlete"

    username: Mapped[str|None] = mapped_column(String)
    access_token: Mapped[str|None] = mapped_column(String)
    refresh_token: Mapped[str|None] = mapped_column(String)
    expire_date: Mapped[int|None] = mapped_column(BigInteger)
    scopes: Mapped[str|None] = mapped_column(String)
    instagram_access_token: Mapped[str|None] = mapped_column(String)
    instagram_expire_date: Mapped[int|None] = mapped_column(BigInteger)
    instagram_user_id: Mapped[int|None] = mapped_column(BigInteger)

    def to_domain(self) -> AthleteDomain:
        return AthleteDomain(
            athlete_id=self.id,
            username=self.username,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expire_date=self.expire_date,
            scopes=self.scopes,
            instagram_access_token=self.instagram_access_token,
            instagram_expire_date=self.instagram_expire_date,
            instagram_user_id=self.instagram_user_id,
        )
