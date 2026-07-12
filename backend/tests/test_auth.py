"""인증 흐름 단위 테스트.

외부 OAuth 호출(Google)은 monkeypatch로 대체한다.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token
from app.models.user import User


# ────────────────────────────────────────────────────────────
# JWT 유틸리티
# ────────────────────────────────────────────────────────────

def test_create_and_decode_token():
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42


def test_decode_invalid_token():
    assert decode_access_token("not.a.token") is None


def test_decode_empty_token():
    assert decode_access_token("") is None


# ────────────────────────────────────────────────────────────
# /health 엔드포인트
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ────────────────────────────────────────────────────────────
# /api/v1/auth/me — 미인증 시 401
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ────────────────────────────────────────────────────────────
# /api/v1/auth/me — 인증된 사용자 정보 반환
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, db: AsyncSession):
    user = User(google_id="google-test-001", email="test@example.com", name="테스트")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    resp = await client.get(
        "/api/v1/auth/me",
        cookies={"access_token": token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["data_sources"] == []


# ────────────────────────────────────────────────────────────
# /api/v1/auth/logout
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


# ────────────────────────────────────────────────────────────
# /api/v1/auth/google/login — state 쿠키 포함 리디렉트
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_google_login_redirects(client: AsyncClient):
    resp = await client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "accounts.google.com" in resp.headers["location"]
    assert "oauth_state" in resp.cookies


# ────────────────────────────────────────────────────────────
# /api/v1/auth/apple-health/connect — 로그인 없으면 401
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_apple_health_connect_requires_login(client: AsyncClient):
    resp = await client.post("/api/v1/auth/apple-health/connect")
    assert resp.status_code == 401


# ────────────────────────────────────────────────────────────
# /api/v1/auth/apple-health/connect — 로그인 후 시크릿+URL 발급
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_apple_health_connect_issues_secret(client: AsyncClient, db: AsyncSession):
    user = User(google_id="google-test-002", email="ah@example.com", name="애플헬스")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    resp = await client.post(
        "/api/v1/auth/apple-health/connect",
        cookies={"access_token": token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["webhook_secret"]
    assert data["webhook_url"].endswith("/api/v1/webhook/apple-health")


@pytest.mark.asyncio
async def test_apple_health_connect_rotates_secret(client: AsyncClient, db: AsyncSession):
    """재연동 시 새 시크릿이 발급되고 이전 시크릿은 무효화된다."""
    user = User(google_id="google-test-003", email="ah2@example.com", name="애플헬스2")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    first = await client.post("/api/v1/auth/apple-health/connect", cookies={"access_token": token})
    second = await client.post("/api/v1/auth/apple-health/connect", cookies={"access_token": token})

    assert first.json()["webhook_secret"] != second.json()["webhook_secret"]


# ────────────────────────────────────────────────────────────
# /api/v1/auth/apple-health/disconnect
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_apple_health_disconnect(client: AsyncClient, db: AsyncSession):
    from sqlalchemy import select

    from app.models.data_source import DataSource

    user = User(google_id="google-test-004", email="ah3@example.com", name="애플헬스3")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    await client.post("/api/v1/auth/apple-health/connect", cookies={"access_token": token})

    resp = await client.delete(
        "/api/v1/auth/apple-health/disconnect", cookies={"access_token": token}
    )
    assert resp.status_code == 204

    remaining = await db.scalar(select(DataSource).where(DataSource.user_id == user.id))
    assert remaining is None
