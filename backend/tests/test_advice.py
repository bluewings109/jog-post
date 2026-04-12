"""LLM 조언 엔드포인트 테스트."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.activity import Activity
from app.models.llm_advice import LLMAdvice
from app.models.user import User


# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────


async def _create_user(db: AsyncSession, suffix: str) -> User:
    user = User(
        google_id=f"g-adv-{suffix}",
        email=f"adv{suffix}@example.com",
        name=f"조언테스트{suffix}",
    )
    db.add(user)
    await db.flush()
    return user


async def _create_activity(db: AsyncSession, user_id: int, strava_id: int = 99001) -> Activity:
    activity = Activity(
        user_id=user_id,
        strava_id=strava_id,
        name="Test Run",
        sport_type="Run",
        start_date=datetime(2024, 6, 1, 5, 30, tzinfo=timezone.utc),
        start_date_local=datetime(2024, 6, 1, 14, 30, tzinfo=timezone.utc),
        distance=10000.0,
        moving_time=3600,
        elapsed_time=3700,
        average_speed=2.78,
        average_heartrate=155.0,
    )
    db.add(activity)
    await db.flush()
    return activity


def _cookie(user_id: int) -> dict:
    return {"access_token": create_access_token(user_id)}


async def _fake_stream(*tokens: str):
    """AsyncGenerator를 흉내 내는 async generator."""
    for token in tokens:
        yield token


# ─────────────────────────────────────────────
# POST /advice/activity/{id}
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_advice_activity_streams_sse(client: AsyncClient, db: AsyncSession):
    """활동 조언이 SSE 형식으로 반환된다."""
    user = await _create_user(db, "act01")
    activity = await _create_activity(db, user.id, strava_id=110001)
    await db.commit()

    mock_llm = MagicMock()
    mock_llm.stream_completion = MagicMock(
        return_value=_fake_stream("좋은 ", "페이스입니다!", " 계속 유지하세요.")
    )
    mock_llm.__class__.__name__ = "MockLLM"

    with patch("app.api.v1.advice.get_llm_client", return_value=mock_llm):
        resp = await client.post(
            f"/api/v1/advice/activity/{activity.id}",
            cookies=_cookie(user.id),
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "좋은 " in body
    assert "[DONE]" in body


@pytest.mark.asyncio
async def test_advice_activity_not_found(client: AsyncClient, db: AsyncSession):
    """존재하지 않는 활동에 조언 요청 시 404."""
    user = await _create_user(db, "act02")
    await db.commit()

    with patch("app.api.v1.advice.get_llm_client"):
        resp = await client.post(
            "/api/v1/advice/activity/99999999",
            cookies=_cookie(user.id),
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_advice_activity_other_user(client: AsyncClient, db: AsyncSession):
    """타인 활동에 조언 요청 시 404."""
    user_a = await _create_user(db, "act03a")
    user_b = await _create_user(db, "act03b")
    activity = await _create_activity(db, user_b.id, strava_id=110002)
    await db.commit()

    with patch("app.api.v1.advice.get_llm_client"):
        resp = await client.post(
            f"/api/v1/advice/activity/{activity.id}",
            cookies=_cookie(user_a.id),
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_advice_activity_saves_to_db(client: AsyncClient, db: AsyncSession):
    """스트리밍 완료 후 LLMAdvice 레코드가 DB에 저장된다."""
    from sqlalchemy import select

    user = await _create_user(db, "act04")
    activity = await _create_activity(db, user.id, strava_id=110003)
    await db.commit()

    mock_llm = MagicMock()
    mock_llm.stream_completion = MagicMock(return_value=_fake_stream("훌륭한 기록입니다!"))
    mock_llm.__class__.__name__ = "MockLLM"

    with patch("app.api.v1.advice.get_llm_client", return_value=mock_llm):
        await client.post(
            f"/api/v1/advice/activity/{activity.id}",
            cookies=_cookie(user.id),
        )

    # DB에 advice 저장됐는지 확인
    row = await db.scalar(
        select(LLMAdvice).where(
            LLMAdvice.user_id == user.id,
            LLMAdvice.activity_id == activity.id,
        )
    )
    assert row is not None
    assert "훌륭한 기록입니다!" in (row.response_text or "")


@pytest.mark.asyncio
async def test_advice_activity_unauthenticated(client: AsyncClient):
    """인증 없이 요청하면 401."""
    resp = await client.post("/api/v1/advice/activity/1")
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# POST /advice/general
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_advice_general_streams_sse(client: AsyncClient, db: AsyncSession):
    """종합 조언이 SSE 형식으로 반환된다."""
    user = await _create_user(db, "gen01")
    await _create_activity(db, user.id, strava_id=120001)
    await db.commit()

    mock_llm = MagicMock()
    mock_llm.stream_completion = MagicMock(return_value=_fake_stream("주 3회 훈련을 권장합니다."))
    mock_llm.__class__.__name__ = "MockLLM"

    with patch("app.api.v1.advice.get_llm_client", return_value=mock_llm):
        resp = await client.post(
            "/api/v1/advice/general",
            cookies=_cookie(user.id),
        )

    assert resp.status_code == 200
    assert "주 3회" in resp.text
    assert "[DONE]" in resp.text


@pytest.mark.asyncio
async def test_advice_general_no_activities(client: AsyncClient, db: AsyncSession):
    """활동이 없어도 스트리밍이 정상 동작한다."""
    user = await _create_user(db, "gen02")
    await db.commit()

    mock_llm = MagicMock()
    mock_llm.stream_completion = MagicMock(return_value=_fake_stream("기록이 없습니다."))
    mock_llm.__class__.__name__ = "MockLLM"

    with patch("app.api.v1.advice.get_llm_client", return_value=mock_llm):
        resp = await client.post(
            "/api/v1/advice/general",
            cookies=_cookie(user.id),
        )

    assert resp.status_code == 200


# ─────────────────────────────────────────────
# GET /advice/history
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_advice_history_empty(client: AsyncClient, db: AsyncSession):
    """조언이 없을 때 빈 목록 반환."""
    user = await _create_user(db, "hist01")
    await db.commit()

    resp = await client.get("/api/v1/advice/history", cookies=_cookie(user.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_advice_history_returns_own_records(client: AsyncClient, db: AsyncSession):
    """자신의 조언 기록만 반환한다."""
    user_a = await _create_user(db, "hist02a")
    user_b = await _create_user(db, "hist02b")

    advice_a = LLMAdvice(
        user_id=user_a.id,
        prompt_context="context A",
        response_text="response A",
        model_used="test",
    )
    advice_b = LLMAdvice(
        user_id=user_b.id,
        prompt_context="context B",
        response_text="response B",
        model_used="test",
    )
    db.add_all([advice_a, advice_b])
    await db.commit()

    resp = await client.get("/api/v1/advice/history", cookies=_cookie(user_a.id))
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["prompt_context"] == "context A"


@pytest.mark.asyncio
async def test_advice_history_unauthenticated(client: AsyncClient):
    """인증 없이 요청하면 401."""
    resp = await client.get("/api/v1/advice/history")
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# 컨텍스트 빌더 단위 테스트
# ─────────────────────────────────────────────


def test_build_activity_context_basic():
    """활동 컨텍스트가 올바르게 생성된다."""
    from app.api.v1.advice import _build_activity_context

    activity = Activity(
        id=1,
        user_id=1,
        strava_id=1,
        name="Morning Run",
        sport_type="Run",
        start_date=datetime(2024, 6, 1, 5, 30, tzinfo=timezone.utc),
        start_date_local=datetime(2024, 6, 1, 14, 30, tzinfo=timezone.utc),
        distance=10000.0,
        moving_time=3600,
        average_speed=2.78,
        average_heartrate=155.0,
    )
    context = _build_activity_context(activity, [])
    assert "10.00 km" in context
    assert "155 bpm" in context
    assert "5:59 /km" in context  # 1000/2.78 ≈ 359.7s → 5:59
    assert "Morning Run" in context


def test_build_general_context_empty():
    """활동이 없으면 '기록 없음' 메시지."""
    from app.api.v1.advice import _build_general_context

    ctx = _build_general_context([])
    assert "없음" in ctx
