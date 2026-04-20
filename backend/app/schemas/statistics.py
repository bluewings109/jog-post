from datetime import datetime

from pydantic import BaseModel


class PeriodStatsItem(BaseModel):
    period_label: str
    period_start: datetime
    activity_count: int
    total_distance: float
    total_moving_time: int
    avg_pace_sec_per_km: float | None
    avg_heartrate: float | None
    total_elevation_gain: float


class WeeklyStatsResponse(BaseModel):
    year: int
    month: int
    weeks: list[PeriodStatsItem]


class MonthlyStatsResponse(BaseModel):
    year: int
    months: list[PeriodStatsItem]


class YearlyStatsResponse(BaseModel):
    years: list[PeriodStatsItem]
