from datetime import datetime
from pydantic import BaseModel

from org.onlypearson.jogpost.common.constants import AspectType
from org.onlypearson.jogpost.common.constants import ObjectType


class StravaWebhookRequest(BaseModel):
    object_type: ObjectType
    # For activity events, the activity's ID. For athlete events, the athlete's ID.
    object_id: int
    aspect_type: AspectType
    """
    For activity update events, keys can contain "title," "type," and "private," which is always "true"
    (activity visibility set to Only You) or "false" (activity visibility set to Followers Only or Everyone).
    For app deauthorization events, there is always an "authorized" : "false" key-value pair.
    """
    updates: dict | None = None
    owner_id: int
    subscription_id: int
    event_time: int

class StravaTokenRefreshResponse(BaseModel):
    access_token: str
    expires_at: int
    expires_in: int
    refresh_token: str

class StravaActivityMapDto(BaseModel):
    id: str
    polyline: str
    summary_polyline: str

class StravaActivityResponse(BaseModel):
    id: int
    name: str
    distance: float
    elapsed_time: float
    type: str
    start_date: datetime
    start_date_local: datetime
    average_heartrate: float | None = None
    max_heartrate: float | None = None
    map: StravaActivityMapDto
