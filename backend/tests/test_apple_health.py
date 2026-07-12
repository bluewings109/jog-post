"""apple_health 서비스 단위 테스트 (필드 매핑, 단위 변환, 1km 구간 계산)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_source import DataSource
from app.models.user import User
from app.services import apple_health


# ─────────────────────────────────────────────
# 단위 변환
# ─────────────────────────────────────────────


def test_parse_distance_km():
    assert apple_health._parse_distance_m({"qty": 10.0, "units": "km"}) == 10000.0


def test_parse_distance_miles():
    result = apple_health._parse_distance_m({"qty": 1.0, "units": "mi"})
    assert abs(result - 1609.344) < 0.01


def test_parse_distance_none():
    assert apple_health._parse_distance_m(None) is None


def test_parse_calories_kj_to_kcal():
    result = apple_health._parse_calories({"qty": 2092.0, "units": "kJ"})
    assert abs(result - 500.0) < 1.0


def test_parse_calories_kcal_passthrough():
    assert apple_health._parse_calories({"qty": 500.0, "units": "kcal"}) == 500.0


# ─────────────────────────────────────────────
# 경로 인코딩 / 고도
# ─────────────────────────────────────────────


def test_encode_route_empty():
    assert apple_health._encode_route([]) is None


def test_encode_route_produces_polyline_string():
    route = [
        {"latitude": 37.5, "longitude": 127.0},
        {"latitude": 37.501, "longitude": 127.001},
    ]
    encoded = apple_health._encode_route(route)
    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_compute_elevation_gain_only_positive():
    route = [{"altitude": 100}, {"altitude": 110}, {"altitude": 105}, {"altitude": 120}]
    # 100→110 (+10), 110→105 (무시), 105→120 (+15) => 25
    assert apple_health._compute_elevation_gain(route) == 25


def test_compute_elevation_gain_insufficient_points():
    assert apple_health._compute_elevation_gain([{"altitude": 100}]) is None


# ─────────────────────────────────────────────
# 1km 구간 계산
# ─────────────────────────────────────────────


def test_compute_splits_short_route_returns_empty():
    assert apple_health._compute_splits([{"latitude": 37.5, "longitude": 127.0, "timestamp": "2024-06-01T00:00:00Z"}]) == []


def test_compute_splits_over_1km():
    """대략 1.5km 이동하는 경로에서 최소 1개 이상의 split이 계산된다."""
    route = [
        {"latitude": 37.5, "longitude": 127.0, "timestamp": "2024-06-01T00:00:00Z"},
        {"latitude": 37.51, "longitude": 127.0, "timestamp": "2024-06-01T00:06:00Z"},  # 약 1.1km
        {"latitude": 37.515, "longitude": 127.0, "timestamp": "2024-06-01T00:09:00Z"},  # 추가 이동
    ]
    splits = apple_health._compute_splits(route)
    assert len(splits) >= 1
    assert splits[0]["split"] == 1
    assert splits[0]["distance"] >= 1000.0


# ─────────────────────────────────────────────
# 시크릿 발급/조회/해제
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_or_rotate_data_source_creates_new(db: AsyncSession):
    user = User(google_id="g-svc-01", email="svc01@example.com", name="서비스테스트1")
    db.add(user)
    await db.flush()
    await db.commit()

    data_source = await apple_health.create_or_rotate_data_source(user.id, db)
    assert data_source.provider == "apple_health"
    assert data_source.webhook_secret


@pytest.mark.asyncio
async def test_create_or_rotate_data_source_rotates_existing(db: AsyncSession):
    user = User(google_id="g-svc-02", email="svc02@example.com", name="서비스테스트2")
    db.add(user)
    await db.flush()
    await db.commit()

    first = await apple_health.create_or_rotate_data_source(user.id, db)
    first_secret = first.webhook_secret
    second = await apple_health.create_or_rotate_data_source(user.id, db)
    assert first_secret != second.webhook_secret


@pytest.mark.asyncio
async def test_get_data_source_by_webhook_secret_found(db: AsyncSession):
    user = User(google_id="g-svc-03", email="svc03@example.com", name="서비스테스트3")
    db.add(user)
    await db.flush()
    ds = DataSource(
        user_id=user.id, provider="apple_health", external_id=str(user.id), webhook_secret="find-me"
    )
    db.add(ds)
    await db.commit()

    found = await apple_health.get_data_source_by_webhook_secret("find-me", db)
    assert found is not None
    assert found.user_id == user.id


@pytest.mark.asyncio
async def test_get_data_source_by_webhook_secret_not_found(db: AsyncSession):
    found = await apple_health.get_data_source_by_webhook_secret("does-not-exist", db)
    assert found is None


@pytest.mark.asyncio
async def test_disconnect_removes_data_source(db: AsyncSession):
    from sqlalchemy import select

    user = User(google_id="g-svc-04", email="svc04@example.com", name="서비스테스트4")
    db.add(user)
    await db.flush()
    await apple_health.create_or_rotate_data_source(user.id, db)

    await apple_health.disconnect(user.id, db)

    remaining = await db.scalar(select(DataSource).where(DataSource.user_id == user.id))
    assert remaining is None


# ─────────────────────────────────────────────
# 워크아웃 upsert / 멱등성
# ─────────────────────────────────────────────

_RUN_WORKOUT = {
    "id": "svc-workout-001",
    "name": "야외 운동",
    "start": "2024-06-01 05:30:00 +0000",
    "end": "2024-06-01 06:30:00 +0000",
    "duration": 3600,
    "activeEnergyBurned": {"qty": 500, "units": "kcal"},
    "distance": {"qty": 10.0, "units": "km"},
    "heartRate": {"min": 100, "avg": 150, "max": 175},
    "route": [],
}


@pytest.mark.asyncio
async def test_sync_workouts_saves_and_maps_fields(db: AsyncSession):
    from sqlalchemy import select

    from app.models.activity import Activity

    user = User(google_id="g-svc-05", email="svc05@example.com", name="서비스테스트5")
    db.add(user)
    await db.flush()
    await db.commit()

    result = await apple_health.sync_workouts({"data": {"workouts": [_RUN_WORKOUT]}}, user.id, db)
    assert result == {"saved": 1, "skipped": 0}

    activity = await db.scalar(
        select(Activity).where(Activity.apple_health_id == "svc-workout-001")
    )
    assert activity is not None
    assert activity.distance == 10000.0
    assert activity.moving_time == 3600
    assert activity.average_heartrate == 150
    assert abs(activity.calories - 500.0) < 0.01


@pytest.mark.asyncio
async def test_sync_workouts_skips_unknown_secret_free_of_side_effects(db: AsyncSession):
    """run이 아닌 운동은 저장하지 않는다."""
    user = User(google_id="g-svc-06", email="svc06@example.com", name="서비스테스트6")
    db.add(user)
    await db.flush()
    await db.commit()

    cycling = {**_RUN_WORKOUT, "id": "svc-workout-cycling", "name": "자전거 타기"}
    result = await apple_health.sync_workouts({"data": {"workouts": [cycling]}}, user.id, db)
    assert result == {"saved": 0, "skipped": 1}
