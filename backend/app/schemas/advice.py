from datetime import datetime

from pydantic import BaseModel


class AdviceHistoryItem(BaseModel):
    id: int
    activity_id: int | None
    prompt_context: str
    response_text: str | None
    model_used: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdviceHistoryResponse(BaseModel):
    items: list[AdviceHistoryItem]
    total: int
