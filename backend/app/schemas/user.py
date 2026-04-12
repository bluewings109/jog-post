from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    picture: str | None

    model_config = {"from_attributes": True}


class DataSourceResponse(BaseModel):
    id: int
    provider: str
    external_id: str
    scopes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(UserResponse):
    data_sources: list[DataSourceResponse]
