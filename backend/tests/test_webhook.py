"""Strava Webhook 엔드포인트 테스트."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.core.security import create_access_token
from app.models.data_source import DataSource
from app.models.user import User


# ─────────────────────────────────────────────
# GET /webhook/strava — hub.challenge 검증
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_verify_success(client: AsyncClient):
    resp = await client.get(
        "/api/v1/webhook/strava",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "abc123",
            "hub.verify_token": settings.STRAVA_WEBHOOK_VERIFY_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"hub.challenge": "abc123"}


@pytest.mark.asyncio
async def test_webhook_verify_wrong_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/webhook/strava",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "abc123",
            "hub.verify_token": "wrong-token",
        },
    )
    assert resp.status_code == 403


# ─────────────────────────────────────────────
# POST /webhook/strava — 이벤트 수신
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_event_returns_200_immediately(client: AsyncClient):
    """이벤트 처리 성공 여부와 관계없이 200을 즉시 반환해야 한다."""
    with patch(
        "app.api.v1.webhook._process_activity", new_callable=AsyncMock
    ):
        resp = await client.post(
            "/api/v1/webhook/strava",
            json={
                "aspect_type": "create",
                "object_type": "activity",
                "object_id": 9999999,
                "owner_id": 12345,
                "event_time": 1700000000,
                "subscription_id": 1,
            },
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_non_activity_event_ignored(client: AsyncClient):
    """activity 외 이벤트(athlete 등)는 BackgroundTask 없이 200만 반환한다."""
    resp = await client.post(
        "/api/v1/webhook/strava",
        json={
            "aspect_type": "update",
            "object_type": "athlete",
            "object_id": 12345,
            "owner_id": 12345,
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_webhook_invalid_json(client: AsyncClient):
    resp = await client.post(
        "/api/v1/webhook/strava",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


# ─────────────────────────────────────────────
# sync_activity_from_webhook — 단위 테스트
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sync_skips_unknown_athlete(db: AsyncSession):
    """data_source가 없는 athlete는 None을 반환한다."""
    from app.services.activity_sync import sync_activity_from_webhook

    result = await sync_activity_from_webhook(
        strava_activity_id=1,
        strava_athlete_id=99999999,
        db=db,
    )
    assert result is None


@pytest.mark.asyncio
async def test_sync_skips_non_run_activity(db: AsyncSession):
    """Run 계열이 아닌 종목은 저장하지 않는다."""
    from app.services.activity_sync import sync_activity_from_webhook

    # 사용자 + Strava 연동 데이터 준비
    user = User(google_id="g-webhook-01", email="wb1@example.com", name="웹훅테스트1")
    db.add(user)
    await db.flush()

    from datetime import datetime, timezone
    ds = DataSource(
        user_id=user.id,
        provider="strava",
        external_id="55555",
        access_token="fake-token",
        refresh_token="fake-refresh",
        token_expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        scopes="activity:read_all",
    )
    db.add(ds)
    await db.commit()

    fake_activity = {
        "id": 88888,
        "sport_type": "Ride",   # 자전거 — 저장 제외 대상
        "type": "Ride",
        "name": "Morning Ride",
        "start_date": "2024-01-01T06:00:00Z",
        "start_date_local": "2024-01-01T15:00:00Z",
        "laps": [],
        "map": {},
    }

    with patch("app.services.activity_sync.strava_api.fetch_activity", return_value=fake_activity), \
         patch("app.services.strava_auth.get_valid_token", return_value="fake-token"):
        result = await sync_activity_from_webhook(88888, 55555, db)

    assert result is None


@pytest.mark.asyncio
async def test_sync_saves_run_activity(db: AsyncSession):
    """Run 활동은 DB에 저장되고 Activity를 반환한다."""
    from app.services.activity_sync import sync_activity_from_webhook

    user = User(google_id="g-webhook-02", email="wb2@example.com", name="웹훅테스트2")
    db.add(user)
    await db.flush()

    from datetime import datetime, timezone
    ds = DataSource(
        user_id=user.id,
        provider="strava",
        external_id="66666",
        access_token="fake-token",
        refresh_token="fake-refresh",
        token_expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        scopes="activity:read_all",
    )
    db.add(ds)
    await db.commit()

    fake_activity = {
        "id": 77777,
        "sport_type": "Run",
        "type": "Run",
        "name": "Morning Run",
        "start_date": "2024-06-01T05:30:00Z",
        "start_date_local": "2024-06-01T14:30:00+09:00",
        "distance": 10000.0,
        "moving_time": 3600,
        "elapsed_time": 3700,
        "total_elevation_gain": 50.0,
        "average_speed": 2.78,
        "average_heartrate": 155.0,
        "laps": [
            {
                "id": 111111,
                "lap_index": 1,
                "name": "Lap 1",
                "elapsed_time": 1800,
                "moving_time": 1800,
                "distance": 5000.0,
                "average_speed": 2.78,
                "average_heartrate": 150.0,
            },
            {
                "id": 111112,
                "lap_index": 2,
                "name": "Lap 2",
                "elapsed_time": 1800,
                "moving_time": 1800,
                "distance": 5000.0,
                "average_speed": 2.78,
                "average_heartrate": 160.0,
            },
        ],
        "map": {"summary_polyline": "abc123", "id": "map001"},
    }

    with patch("app.services.activity_sync.strava_api.fetch_activity", return_value=fake_activity), \
         patch("app.services.strava_auth.get_valid_token", return_value="fake-token"):
        result = await sync_activity_from_webhook(77777, 66666, db)

    assert result is not None
    assert result.strava_id == 77777
    assert result.sport_type == "Run"
    assert result.distance == 10000.0

    # laps는 lazy-load이므로 별도 쿼리로 확인
    from sqlalchemy import select, func
    from app.models.lap import Lap
    lap_count = await db.scalar(select(func.count()).where(Lap.activity_id == result.id))
    assert lap_count == 2


@pytest.mark.asyncio
async def test_sync_is_idempotent(db: AsyncSession):
    """같은 활동을 두 번 동기화해도 중복 저장되지 않는다."""
    from sqlalchemy import select, func
    from app.models.activity import Activity
    from app.services.activity_sync import sync_activity_from_webhook

    user = User(google_id="g-webhook-03", email="wb3@example.com", name="웹훅테스트3")
    db.add(user)
    await db.flush()

    from datetime import datetime, timezone
    ds = DataSource(
        user_id=user.id,
        provider="strava",
        external_id="77777",
        access_token="fake-token",
        refresh_token="fake-refresh",
        token_expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        scopes="activity:read_all",
    )
    db.add(ds)
    await db.commit()

    fake_activity = {
        "id": 55555,
        "sport_type": "Run",
        "type": "Run",
        "name": "Evening Run",
        "start_date": "2024-06-02T10:00:00Z",
        "start_date_local": "2024-06-02T19:00:00+09:00",
        "distance": 5000.0,
        "moving_time": 1800,
        "elapsed_time": 1900,
        "laps": [],
        "map": {},
    }

    with patch("app.services.activity_sync.strava_api.fetch_activity", return_value=fake_activity), \
         patch("app.services.strava_auth.get_valid_token", return_value="fake-token"):
        await sync_activity_from_webhook(55555, 77777, db)
        await sync_activity_from_webhook(55555, 77777, db)

    count = await db.scalar(select(func.count()).where(Activity.strava_id == 55555))
    assert count == 1
