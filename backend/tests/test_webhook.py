"""Apple Health(Health Auto Export) Webhook 엔드포인트 테스트."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_source import DataSource
from app.models.user import User


async def _create_user_with_secret(db: AsyncSession, suffix: str, secret: str) -> User:
    user = User(google_id=f"g-wh-{suffix}", email=f"wh{suffix}@example.com", name=f"웹훅{suffix}")
    db.add(user)
    await db.flush()

    ds = DataSource(
        user_id=user.id,
        provider="apple_health",
        external_id=str(user.id),
        webhook_secret=secret,
    )
    db.add(ds)
    await db.commit()
    return user


_RUN_WORKOUT = {
    "id": "workout-001",
    "name": "Running",
    "start": "2024-06-01 05:30:00 +0000",
    "end": "2024-06-01 06:30:00 +0000",
    "duration": 3600,
    "activeEnergyBurned": {"qty": 500, "units": "kcal"},
    "distance": {"qty": 10.0, "units": "km"},
    "heartRate": {"min": 100, "avg": 150, "max": 175},
    "route": [],
}


@pytest.mark.asyncio
async def test_webhook_missing_secret(client: AsyncClient):
    resp = await client.post("/api/v1/webhook/apple-health", json={"data": {"workouts": []}})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_wrong_secret(client: AsyncClient, db: AsyncSession):
    await _create_user_with_secret(db, "01", "correct-secret")

    resp = await client.post(
        "/api/v1/webhook/apple-health",
        json={"data": {"workouts": []}},
        headers={"X-Webhook-Secret": "wrong-secret"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_invalid_json(client: AsyncClient, db: AsyncSession):
    await _create_user_with_secret(db, "02", "secret-02")

    resp = await client.post(
        "/api/v1/webhook/apple-health",
        content=b"not-json",
        headers={"X-Webhook-Secret": "secret-02", "Content-Type": "application/json"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_webhook_saves_run_workout(client: AsyncClient, db: AsyncSession):
    await _create_user_with_secret(db, "03", "secret-03")

    resp = await client.post(
        "/api/v1/webhook/apple-health",
        json={"data": {"workouts": [_RUN_WORKOUT]}},
        headers={"X-Webhook-Secret": "secret-03"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"saved": 1, "skipped": 0}


@pytest.mark.asyncio
async def test_webhook_skips_non_run_workout(client: AsyncClient, db: AsyncSession):
    await _create_user_with_secret(db, "04", "secret-04")

    cycling = {**_RUN_WORKOUT, "id": "workout-cycling", "name": "Cycling"}
    resp = await client.post(
        "/api/v1/webhook/apple-health",
        json={"data": {"workouts": [cycling]}},
        headers={"X-Webhook-Secret": "secret-04"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"saved": 0, "skipped": 1}


@pytest.mark.asyncio
async def test_webhook_is_idempotent(client: AsyncClient, db: AsyncSession):
    """같은 apple_health_id의 운동을 두 번 보내도 중복 저장되지 않는다."""
    from sqlalchemy import func, select

    from app.models.activity import Activity

    await _create_user_with_secret(db, "05", "secret-05")

    workout = {**_RUN_WORKOUT, "id": "workout-idempotent"}
    for _ in range(2):
        resp = await client.post(
            "/api/v1/webhook/apple-health",
            json={"data": {"workouts": [workout]}},
            headers={"X-Webhook-Secret": "secret-05"},
        )
        assert resp.status_code == 200

    count = await db.scalar(
        select(func.count()).where(Activity.apple_health_id == "workout-idempotent")
    )
    assert count == 1


@pytest.mark.asyncio
async def test_webhook_saves_multiple_workouts_in_one_request(client: AsyncClient, db: AsyncSession):
    await _create_user_with_secret(db, "06", "secret-06")

    workouts = [
        {**_RUN_WORKOUT, "id": "workout-multi-1"},
        {**_RUN_WORKOUT, "id": "workout-multi-2"},
    ]
    resp = await client.post(
        "/api/v1/webhook/apple-health",
        json={"data": {"workouts": workouts}},
        headers={"X-Webhook-Secret": "secret-06"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"saved": 2, "skipped": 0}
