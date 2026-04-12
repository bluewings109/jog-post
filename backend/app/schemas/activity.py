from datetime import datetime

from pydantic import BaseModel, computed_field


class LapResponse(BaseModel):
    id: int
    strava_id: int
    lap_index: int
    name: str | None
    elapsed_time: int | None
    moving_time: int | None
    distance: float | None
    average_speed: float | None
    max_speed: float | None
    average_cadence: float | None
    average_heartrate: float | None
    max_heartrate: float | None
    total_elevation_gain: float | None
    pace_zone: int | None

    model_config = {"from_attributes": True}


class ActivityResponse(BaseModel):
    id: int
    strava_id: int
    name: str | None
    sport_type: str | None
    start_date: datetime
    start_date_local: datetime
    timezone: str | None
    distance: float | None
    moving_time: int | None
    elapsed_time: int | None
    total_elevation_gain: float | None
    average_speed: float | None
    max_speed: float | None
    average_heartrate: float | None
    max_heartrate: float | None
    average_cadence: float | None
    calories: float | None
    suffer_score: int | None
    summary_polyline: str | None
    achievement_count: int
    kudos_count: int
    pr_count: int
    trainer: bool
    commute: bool

    @computed_field
    @property
    def average_pace_sec_per_km(self) -> float | None:
        """평균 페이스 (초/km). average_speed(m/s) 기반으로 계산."""
        if not self.average_speed or self.average_speed <= 0:
            return None
        return 1000 / self.average_speed

    model_config = {"from_attributes": True}


class ActivityDetailResponse(ActivityResponse):
    laps: list[LapResponse] = []


class ActivitiesPageResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    per_page: int
