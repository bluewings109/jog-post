"""Apple Health(Health Auto Export) 데이터 소스 연동 및 활동 동기화 로직.

Health Auto Export 앱은 OAuth 없이 커스텀 웹훅 시크릿으로 인증하며,
기간 기준으로 운동 데이터를 배치 전송한다(같은 운동이 재전송될 수 있어 멱등성이 중요하다).
"""

import hmac
import logging
import secrets
from datetime import datetime

import polyline
from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.data_source import DataSource

logger = logging.getLogger(__name__)

_PROVIDER = "apple_health"
_KJ_PER_KCAL = 4.184
_MILES_TO_METERS = 1609.344
_SPLIT_DISTANCE_M = 1000.0


# ────────────────────────────────────────────────────────────
# 연동(시크릿) 관리
# ────────────────────────────────────────────────────────────

def generate_webhook_secret() -> str:
    return secrets.token_urlsafe(32)


async def create_or_rotate_data_source(user_id: int, db: AsyncSession) -> DataSource:
    """Apple Health 연동을 생성하거나 시크릿을 재발급한다."""
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == user_id, DataSource.provider == _PROVIDER)
    )
    data_source = result.scalar_one_or_none()

    secret = generate_webhook_secret()
    if data_source is None:
        data_source = DataSource(
            user_id=user_id,
            provider=_PROVIDER,
            external_id=str(user_id),
            webhook_secret=secret,
        )
        db.add(data_source)
    else:
        data_source.webhook_secret = secret

    await db.commit()
    await db.refresh(data_source)
    return data_source


async def get_data_source_by_webhook_secret(secret: str, db: AsyncSession) -> DataSource | None:
    """웹훅 요청의 시크릿으로 소유 사용자를 조회한다."""
    result = await db.execute(
        select(DataSource).where(DataSource.provider == _PROVIDER, DataSource.webhook_secret.is_not(None))
    )
    for data_source in result.scalars().all():
        if data_source.webhook_secret and hmac.compare_digest(data_source.webhook_secret, secret):
            return data_source
    return None


async def disconnect(user_id: int, db: AsyncSession) -> None:
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == user_id, DataSource.provider == _PROVIDER)
    )
    data_source = result.scalar_one_or_none()
    if data_source is not None:
        await db.delete(data_source)
        await db.commit()


# ────────────────────────────────────────────────────────────
# 워크아웃 동기화
# ────────────────────────────────────────────────────────────

async def sync_workouts(payload: dict, user_id: int, db: AsyncSession) -> dict:
    """Health Auto Export 웹훅 페이로드에서 운동 목록을 동기화한다."""
    workouts = payload.get("data", {}).get("workouts", [])

    saved = 0
    skipped = 0
    for raw in workouts:
        try:
            activity = await _upsert_activity(raw, user_id, db)
        except Exception:
            logger.exception("Failed to process Apple Health workout id=%s", raw.get("id"))
            skipped += 1
            continue

        if activity is None:
            skipped += 1
        else:
            saved += 1

    return {"saved": saved, "skipped": skipped}


async def _upsert_activity(raw: dict, user_id: int, db: AsyncSession) -> Activity | None:
    name = raw.get("name") or ""
    if "run" not in name.lower():
        # TODO: 이름 기반 필터가 로케일에 취약함이 확인됨(한국어 "야외 운동" 등).
        # 정확한 운동 타입 필드를 찾기 위해 전체 payload를 임시로 로깅한다.
        logger.info(
            "Skipping non-running workout: name=%s keys=%s raw=%s",
            name,
            list(raw.keys()),
            {k: v for k, v in raw.items() if k != "route" and k != "heartRateData"},
        )
        return None

    apple_health_id = raw.get("id")
    if not apple_health_id:
        logger.warning("Workout missing id, skipping: name=%s", name)
        return None

    route = raw.get("route") or []
    distance_m = _parse_distance_m(raw.get("distance"))
    duration_s = raw.get("duration")
    moving_time = int(duration_s) if duration_s else None
    average_speed = (distance_m / moving_time) if distance_m and moving_time else None

    heart_rate = raw.get("heartRate") or {}

    fields = dict(
        user_id=user_id,
        name=name,
        type=name,
        sport_type=name,
        start_date=_parse_dt(raw.get("start")),
        start_date_local=_parse_dt(raw.get("start")),
        distance=distance_m,
        moving_time=moving_time,
        elapsed_time=moving_time,
        total_elevation_gain=_compute_elevation_gain(route),
        average_speed=average_speed,
        average_heartrate=heart_rate.get("avg"),
        max_heartrate=heart_rate.get("max"),
        calories=_parse_calories(raw.get("activeEnergyBurned")),
        summary_polyline=_encode_route(route),
        raw_json={**raw, "computed_splits": _compute_splits(route)},
    )

    result = await db.execute(select(Activity).where(Activity.apple_health_id == apple_health_id))
    activity = result.scalar_one_or_none()

    if activity is None:
        activity = Activity(apple_health_id=apple_health_id, **fields)
        db.add(activity)
    else:
        for k, v in fields.items():
            setattr(activity, k, v)

    await db.commit()
    await db.refresh(activity)
    return activity


# ────────────────────────────────────────────────────────────
# 필드 변환 헬퍼
# ────────────────────────────────────────────────────────────

def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.now()
    return date_parser.parse(value)


def _parse_distance_m(distance: dict | None) -> float | None:
    if not distance or distance.get("qty") is None:
        return None
    qty = float(distance["qty"])
    units = distance.get("units", "km")
    if units == "mi":
        return qty * _MILES_TO_METERS
    return qty * 1000  # km 기본


def _parse_calories(energy: dict | None) -> float | None:
    if not energy or energy.get("qty") is None:
        return None
    qty = float(energy["qty"])
    if energy.get("units") == "kJ":
        return qty / _KJ_PER_KCAL
    return qty


def _encode_route(route: list[dict]) -> str | None:
    points = [
        (p["latitude"], p["longitude"])
        for p in route
        if p.get("latitude") is not None and p.get("longitude") is not None
    ]
    if not points:
        return None
    return polyline.encode(points)


def _compute_elevation_gain(route: list[dict]) -> float | None:
    altitudes = [p["altitude"] for p in route if p.get("altitude") is not None]
    if len(altitudes) < 2:
        return None
    gain = 0.0
    for prev, curr in zip(altitudes, altitudes[1:]):
        if curr > prev:
            gain += curr - prev
    return gain


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _compute_splits(route: list[dict]) -> list[dict]:
    """route의 좌표+timestamp로 1km 구간별 페이스를 계산한다 (Strava splits_metric과 유사한 구조)."""
    points = [
        p for p in route
        if p.get("latitude") is not None and p.get("longitude") is not None and p.get("timestamp")
    ]
    if len(points) < 2:
        return []

    splits: list[dict] = []
    cumulative_distance = 0.0
    split_start_distance = 0.0
    split_start_time = date_parser.parse(points[0]["timestamp"])
    split_index = 1

    prev = points[0]
    prev_time = split_start_time

    for point in points[1:]:
        curr_time = date_parser.parse(point["timestamp"])
        segment_distance = _haversine_m(
            prev["latitude"], prev["longitude"], point["latitude"], point["longitude"]
        )
        cumulative_distance += segment_distance

        if cumulative_distance - split_start_distance >= _SPLIT_DISTANCE_M:
            elapsed = (curr_time - split_start_time).total_seconds()
            split_distance = cumulative_distance - split_start_distance
            splits.append({
                "split": split_index,
                "distance": split_distance,
                "elapsed_time": int(elapsed) if elapsed else None,
                "average_speed": (split_distance / elapsed) if elapsed else None,
            })
            split_index += 1
            split_start_distance = cumulative_distance
            split_start_time = curr_time

        prev = point
        prev_time = curr_time

    # 마지막 남은 구간(1km 미만)도 기록
    remaining = cumulative_distance - split_start_distance
    if remaining > 0:
        elapsed = (prev_time - split_start_time).total_seconds()
        splits.append({
            "split": split_index,
            "distance": remaining,
            "elapsed_time": int(elapsed) if elapsed else None,
            "average_speed": (remaining / elapsed) if elapsed else None,
        })

    return splits
