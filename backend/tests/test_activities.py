"""활동 API 엔드포인트 테스트."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.activity import Activity
from app.models.data_source import DataSource
from app.models.lap import Lap
from app.models.user import User


# ─────────────────────────────────────────────
# 헬퍼: 사용자 + 활동 생성
# ─────────────────────────────────────────────


async def _create_user(db: AsyncSession, suffix: str = "01") -> User:
    user = User(
        google_id=f"g-act-{suffix}",
        email=f"act{suffix}@example.com",
        name=f"테스트유저{suffix}",
    )
    db.add(user)
    await db.flush()
    return user


async def _create_activity(
    db: AsyncSession,
    user_id: int,
    strava_id: int = 10001,
    start_date: datetime | None = None,
    distance: float = 5000.0,
) -> Activity:
    if start_date is None:
        start_date = datetime(2024, 6, 1, 5, 30, tzinfo=timezone.utc)
    activity = Activity(
        user_id=user_id,
        strava_id=strava_id,
        name="Morning Run",
        sport_type="Run",
        start_date=start_date,
        start_date_local=start_date,
        distance=distance,
        moving_time=1800,
        elapsed_time=1850,
        average_speed=2.78,
    )
    db.add(activity)
    await db.flush()
    return activity


def _auth_cookie(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"access_token": token}


# ─────────────────────────────────────────────
# GET /activities — 목록 조회
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_activities_empty(client: AsyncClient, db: AsyncSession):
    """활동이 없을 때 빈 목록을 반환한다."""
    user = await _create_user(db, "list01")
    await db.commit()

    resp = await client.get("/api/v1/activities", cookies=_auth_cookie(user.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_activities_returns_own_activities(client: AsyncClient, db: AsyncSession):
    """자신의 활동만 반환한다 (타인 활동 미포함)."""
    user_a = await _create_user(db, "list02a")
    user_b = await _create_user(db, "list02b")
    await _create_activity(db, user_a.id, strava_id=20001)
    await _create_activity(db, user_b.id, strava_id=20002)
    await db.commit()

    resp = await client.get("/api/v1/activities", cookies=_auth_cookie(user_a.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["strava_id"] == 20001


@pytest.mark.asyncio
async def test_list_activities_pagination(client: AsyncClient, db: AsyncSession):
    """페이지네이션이 올바르게 동작한다."""
    user = await _create_user(db, "list03")
    for i in range(5):
        await _create_activity(
            db,
            user.id,
            strava_id=30000 + i,
            start_date=datetime(2024, 6, i + 1, tzinfo=timezone.utc),
        )
    await db.commit()

    resp = await client.get(
        "/api/v1/activities", params={"page": 1, "per_page": 2}, cookies=_auth_cookie(user.id)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["per_page"] == 2

    resp2 = await client.get(
        "/api/v1/activities", params={"page": 3, "per_page": 2}, cookies=_auth_cookie(user.id)
    )
    assert len(resp2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_list_activities_ordered_by_latest(client: AsyncClient, db: AsyncSession):
    """최신순(start_date DESC)으로 정렬된다."""
    user = await _create_user(db, "list04")
    await _create_activity(
        db, user.id, strava_id=40001, start_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    await _create_activity(
        db, user.id, strava_id=40002, start_date=datetime(2024, 6, 1, tzinfo=timezone.utc)
    )
    await db.commit()

    resp = await client.get("/api/v1/activities", cookies=_auth_cookie(user.id))
    items = resp.json()["items"]
    assert items[0]["strava_id"] == 40002  # 더 최신
    assert items[1]["strava_id"] == 40001


@pytest.mark.asyncio
async def test_list_activities_date_filter(client: AsyncClient, db: AsyncSession):
    """start_date / end_date 필터가 동작한다."""
    user = await _create_user(db, "list05")
    await _create_activity(
        db, user.id, strava_id=50001, start_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
    )
    await _create_activity(
        db, user.id, strava_id=50002, start_date=datetime(2024, 3, 15, tzinfo=timezone.utc)
    )
    await _create_activity(
        db, user.id, strava_id=50003, start_date=datetime(2024, 6, 15, tzinfo=timezone.utc)
    )
    await db.commit()

    resp = await client.get(
        "/api/v1/activities",
        params={"start_date": "2024-02-01T00:00:00Z", "end_date": "2024-05-01T00:00:00Z"},
        cookies=_auth_cookie(user.id),
    )
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["strava_id"] == 50002


@pytest.mark.asyncio
async def test_list_activities_includes_pace(client: AsyncClient, db: AsyncSession):
    """응답에 average_pace_sec_per_km computed field가 포함된다."""
    user = await _create_user(db, "list06")
    await _create_activity(db, user.id, strava_id=60001)
    await db.commit()

    resp = await client.get("/api/v1/activities", cookies=_auth_cookie(user.id))
    item = resp.json()["items"][0]
    assert "average_pace_sec_per_km" in item
    # average_speed=2.78 m/s → 1000/2.78 ≈ 359.7 sec/km
    assert abs(item["average_pace_sec_per_km"] - 1000 / 2.78) < 0.1


@pytest.mark.asyncio
async def test_list_activities_unauthenticated(client: AsyncClient):
    """인증 없이 요청하면 401을 반환한다."""
    resp = await client.get("/api/v1/activities")
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# GET /activities/{id} — 상세 조회
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_activity_detail(client: AsyncClient, db: AsyncSession):
    """활동 상세와 랩 목록을 반환한다."""
    user = await _create_user(db, "det01")
    activity = await _create_activity(db, user.id, strava_id=70001)
    lap = Lap(
        activity_id=activity.id,
        strava_id=700010,
        lap_index=1,
        name="Lap 1",
        elapsed_time=1800,
        moving_time=1800,
        distance=5000.0,
        average_speed=2.78,
    )
    db.add(lap)
    await db.commit()

    resp = await client.get(
        f"/api/v1/activities/{activity.id}", cookies=_auth_cookie(user.id)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["strava_id"] == 70001
    assert len(data["laps"]) == 1
    assert data["laps"][0]["lap_index"] == 1


@pytest.mark.asyncio
async def test_get_activity_detail_not_found(client: AsyncClient, db: AsyncSession):
    """존재하지 않는 활동 조회 시 404를 반환한다."""
    user = await _create_user(db, "det02")
    await db.commit()

    resp = await client.get("/api/v1/activities/99999999", cookies=_auth_cookie(user.id))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_activity_detail_other_user(client: AsyncClient, db: AsyncSession):
    """타인의 활동 조회 시 404를 반환한다."""
    user_a = await _create_user(db, "det03a")
    user_b = await _create_user(db, "det03b")
    activity = await _create_activity(db, user_b.id, strava_id=80001)
    await db.commit()

    resp = await client.get(
        f"/api/v1/activities/{activity.id}", cookies=_auth_cookie(user_a.id)
    )
    assert resp.status_code == 404


# ─────────────────────────────────────────────
# DELETE /activities/{id}
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_activity(client: AsyncClient, db: AsyncSession):
    """활동 삭제 후 204를 반환하고 DB에서 제거된다."""
    from sqlalchemy import select

    user = await _create_user(db, "del01")
    activity = await _create_activity(db, user.id, strava_id=90001)
    await db.commit()

    resp = await client.delete(
        f"/api/v1/activities/{activity.id}", cookies=_auth_cookie(user.id)
    )
    assert resp.status_code == 204

    row = await db.get(Activity, activity.id)
    assert row is None


@pytest.mark.asyncio
async def test_delete_activity_not_found(client: AsyncClient, db: AsyncSession):
    """존재하지 않는 활동 삭제 시 404를 반환한다."""
    user = await _create_user(db, "del02")
    await db.commit()

    resp = await client.delete("/api/v1/activities/99999999", cookies=_auth_cookie(user.id))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_activity_other_user(client: AsyncClient, db: AsyncSession):
    """타인의 활동은 삭제할 수 없다."""
    user_a = await _create_user(db, "del03a")
    user_b = await _create_user(db, "del03b")
    activity = await _create_activity(db, user_b.id, strava_id=90002)
    await db.commit()

    resp = await client.delete(
        f"/api/v1/activities/{activity.id}", cookies=_auth_cookie(user_a.id)
    )
    assert resp.status_code == 404


# ─────────────────────────────────────────────
# POST /activities/sync
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_activities_no_strava_connection(client: AsyncClient, db: AsyncSession):
    """Strava 연동이 없으면 400을 반환한다."""
    user = await _create_user(db, "sync01")
    await db.commit()

    resp = await client.post("/api/v1/activities/sync", cookies=_auth_cookie(user.id))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_sync_activities_with_strava(client: AsyncClient, db: AsyncSession):
    """Strava 연동이 있으면 sync를 실행하고 synced 카운트를 반환한다."""
    user = await _create_user(db, "sync02")
    ds = DataSource(
        user_id=user.id,
        provider="strava",
        external_id="99887766",
        access_token="fake-token",
        refresh_token="fake-refresh",
        token_expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        scopes="activity:read_all",
    )
    db.add(ds)
    await db.commit()

    with patch(
        "app.api.v1.activities.sync_activities_bulk", new_callable=AsyncMock, return_value=3
    ):
        resp = await client.post("/api/v1/activities/sync", cookies=_auth_cookie(user.id))

    assert resp.status_code == 200
    assert resp.json() == {"synced": 3}
