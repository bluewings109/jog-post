"""인증 흐름 단위 테스트.

외부 OAuth 호출(Google, Strava)은 monkeypatch로 대체한다.
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
# /api/v1/auth/strava/connect — 로그인 없으면 401
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_strava_connect_requires_login(client: AsyncClient):
    resp = await client.get("/api/v1/auth/strava/connect", follow_redirects=False)
    assert resp.status_code == 401


# ────────────────────────────────────────────────────────────
# /api/v1/auth/strava/connect — 로그인 후 Strava OAuth로 리디렉트
# ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_strava_connect_redirects(client: AsyncClient, db: AsyncSession):
    user = User(google_id="google-test-002", email="strava@example.com", name="스트라바")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    resp = await client.get(
        "/api/v1/auth/strava/connect",
        cookies={"access_token": token},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert "strava.com" in resp.headers["location"]
