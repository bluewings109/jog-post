"""Strava 활동 데이터를 DB에 동기화하는 비즈니스 로직.

Webhook 이벤트와 수동 동기화 모두 이 모듈을 사용한다.
"""

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.lap import Lap
from app.services import strava_api, strava_auth

logger = logging.getLogger(__name__)

# 저장 대상 sport_type (Strava 기준)
_RUN_SPORT_TYPES = {"Run", "TrailRun", "VirtualRun", "Treadmill"}


async def sync_activity_from_webhook(
    strava_activity_id: int,
    strava_athlete_id: int,
    db: AsyncSession,
) -> Activity | None:
    """Webhook 이벤트에서 활동 하나를 동기화한다.

    1. athlete_id로 data_source 조회
    2. 유효한 access_token 확보 (필요 시 갱신)
    3. Strava API로 활동 상세 조회
    4. Run 계열 종목만 저장
    5. activities + laps upsert

    Returns:
        저장된 Activity, 또는 저장 대상이 아닌 경우 None
    """
    data_source = await strava_auth.get_data_source_by_strava_athlete_id(
        strava_athlete_id, db
    )
    if data_source is None:
        logger.warning("No data_source for Strava athlete_id=%s", strava_athlete_id)
        return None

    access_token = await strava_auth.get_valid_token(data_source, db)

    try:
        raw = await strava_api.fetch_activity(strava_activity_id, access_token)
    except Exception:
        logger.exception("Failed to fetch activity %s from Strava", strava_activity_id)
        return None

    sport_type = raw.get("sport_type") or raw.get("type", "")
    if sport_type not in _RUN_SPORT_TYPES:
        logger.info("Skipping activity %s: sport_type=%s", strava_activity_id, sport_type)
        return None

    return await _upsert_activity(raw, data_source.user_id, db)


async def sync_activities_bulk(
    strava_athlete_id: int,
    db: AsyncSession,
    *,
    max_pages: int = 10,
) -> int:
    """과거 활동을 일괄 동기화한다 (수동 동기화용).

    Strava Rate Limit(15분당 200회)을 고려해 최대 10페이지(300개)로 제한한다.

    Returns:
        저장된 활동 수
    """
    data_source = await strava_auth.get_data_source_by_strava_athlete_id(
        strava_athlete_id, db
    )
    if data_source is None:
        return 0

    access_token = await strava_auth.get_valid_token(data_source, db)
    saved = 0

    for page in range(1, max_pages + 1):
        activities = await strava_api.fetch_athlete_activities(
            access_token, page=page, per_page=30
        )
        if not activities:
            break

        for summary in activities:
            sport_type = summary.get("sport_type") or summary.get("type", "")
            if sport_type not in _RUN_SPORT_TYPES:
                continue
            # 요약 응답에 laps가 없으므로 상세 조회
            # 429는 상위로 전파해서 엔드포인트에서 처리
            try:
                raw = await strava_api.fetch_activity(summary["id"], access_token)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise
                logger.exception("Failed to fetch activity %s", summary["id"])
                continue
            except Exception:
                logger.exception("Failed to fetch activity %s", summary["id"])
                continue
            await _upsert_activity(raw, data_source.user_id, db)
            saved += 1

    return saved


# ────────────────────────────────────────────────────────────
# 내부 헬퍼
# ────────────────────────────────────────────────────────────

async def _upsert_activity(raw: dict, user_id: int, db: AsyncSession) -> Activity:
    """Strava 원본 응답으로 Activity + Lap을 upsert한다."""
    strava_id = raw["id"]

    result = await db.execute(select(Activity).where(Activity.strava_id == strava_id))
    activity = result.scalar_one_or_none()

    start_date = _parse_dt(raw.get("start_date"))
    start_date_local = _parse_dt(raw.get("start_date_local"))

    fields = dict(
        user_id=user_id,
        name=raw.get("name"),
        type=raw.get("type"),
        sport_type=raw.get("sport_type"),
        start_date=start_date,
        start_date_local=start_date_local,
        timezone=raw.get("timezone"),
        distance=raw.get("distance"),
        moving_time=raw.get("moving_time"),
        elapsed_time=raw.get("elapsed_time"),
        total_elevation_gain=raw.get("total_elevation_gain"),
        average_speed=raw.get("average_speed"),
        max_speed=raw.get("max_speed"),
        average_cadence=raw.get("average_cadence"),
        average_heartrate=raw.get("average_heartrate"),
        max_heartrate=raw.get("max_heartrate"),
        calories=raw.get("calories"),
        suffer_score=raw.get("suffer_score"),
        summary_polyline=raw.get("map", {}).get("summary_polyline"),
        map_id=raw.get("map", {}).get("id"),
        achievement_count=raw.get("achievement_count", 0),
        kudos_count=raw.get("kudos_count", 0),
        pr_count=raw.get("pr_count", 0),
        trainer=raw.get("trainer", False),
        commute=raw.get("commute", False),
        manual=raw.get("manual", False),
        raw_json=raw,
    )

    if activity is None:
        activity = Activity(strava_id=strava_id, **fields)
        db.add(activity)
        await db.flush()   # activity.id 확보
    else:
        for k, v in fields.items():
            setattr(activity, k, v)
        await db.flush()

    await _upsert_laps(raw.get("laps", []), activity.id, db)
    await db.commit()
    await db.refresh(activity)
    return activity


async def _upsert_laps(laps_data: list[dict], activity_id: int, db: AsyncSession) -> None:
    """랩 목록을 upsert한다. 기존 랩은 갱신, 새 랩은 추가한다."""
    for lap_raw in laps_data:
        strava_id = lap_raw["id"]
        result = await db.execute(select(Lap).where(Lap.strava_id == strava_id))
        lap = result.scalar_one_or_none()

        fields = dict(
            activity_id=activity_id,
            lap_index=lap_raw.get("lap_index", 0),
            name=lap_raw.get("name"),
            elapsed_time=lap_raw.get("elapsed_time"),
            moving_time=lap_raw.get("moving_time"),
            distance=lap_raw.get("distance"),
            average_speed=lap_raw.get("average_speed"),
            max_speed=lap_raw.get("max_speed"),
            average_cadence=lap_raw.get("average_cadence"),
            average_heartrate=lap_raw.get("average_heartrate"),
            max_heartrate=lap_raw.get("max_heartrate"),
            total_elevation_gain=lap_raw.get("total_elevation_gain"),
            pace_zone=lap_raw.get("pace_zone"),
        )

        if lap is None:
            db.add(Lap(strava_id=strava_id, **fields))
        else:
            for k, v in fields.items():
                setattr(lap, k, v)


def _parse_dt(value: str | None) -> datetime:
    """Strava ISO 8601 문자열을 timezone-aware datetime으로 변환한다."""
    if not value:
        return datetime.now(tz=timezone.utc)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
