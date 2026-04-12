import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.data_source import DataSource

_STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
_STRAVA_TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
_SCOPES = "activity:read_all"
_PROVIDER = "strava"


def build_connect_url(redirect_uri: str) -> tuple[str, str]:
    """Strava 데이터 연동 OAuth URL과 state 값을 반환한다."""
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "state": state,
        "approval_prompt": "auto",
    }
    return f"{_STRAVA_AUTH_URL}?{urlencode(params)}", state


async def exchange_code(code: str) -> dict:
    """Authorization code를 Strava access_token으로 교환한다."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _STRAVA_TOKEN_URL,
            data={
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_token(data_source: DataSource, db: AsyncSession) -> DataSource:
    """access_token이 만료됐을 때 갱신하고 DB를 업데이트한다."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _STRAVA_TOKEN_URL,
            data={
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
                "refresh_token": data_source.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    data_source.access_token = token_data["access_token"]
    data_source.refresh_token = token_data["refresh_token"]
    data_source.token_expires_at = datetime.fromtimestamp(
        token_data["expires_at"], tz=timezone.utc
    )
    await db.commit()
    await db.refresh(data_source)
    return data_source


async def get_valid_token(data_source: DataSource, db: AsyncSession) -> str:
    """만료 여부를 확인하고 유효한 access_token을 반환한다."""
    if data_source.token_expires_at <= datetime.now(tz=timezone.utc):
        data_source = await refresh_token(data_source, db)
    return data_source.access_token


async def upsert_data_source(user_id: int, token_data: dict, db: AsyncSession) -> DataSource:
    """Strava 토큰 응답으로 data_sources 행을 생성 또는 업데이트한다."""
    athlete = token_data["athlete"]
    external_id = str(athlete["id"])
    expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)

    result = await db.execute(
        select(DataSource).where(
            DataSource.user_id == user_id,
            DataSource.provider == _PROVIDER,
        )
    )
    data_source = result.scalar_one_or_none()

    if data_source is None:
        data_source = DataSource(
            user_id=user_id,
            provider=_PROVIDER,
            external_id=external_id,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_expires_at=expires_at,
            scopes=token_data.get("scope", _SCOPES),
        )
        db.add(data_source)
    else:
        data_source.external_id = external_id
        data_source.access_token = token_data["access_token"]
        data_source.refresh_token = token_data["refresh_token"]
        data_source.token_expires_at = expires_at
        data_source.scopes = token_data.get("scope", _SCOPES)

    await db.commit()
    await db.refresh(data_source)
    return data_source


async def get_strava_data_source(user_id: int, db: AsyncSession) -> DataSource | None:
    """사용자의 Strava 연동 정보를 조회한다."""
    result = await db.execute(
        select(DataSource).where(
            DataSource.user_id == user_id,
            DataSource.provider == _PROVIDER,
        )
    )
    return result.scalar_one_or_none()


async def get_data_source_by_strava_athlete_id(
    strava_athlete_id: int, db: AsyncSession
) -> DataSource | None:
    """Strava athlete ID로 data_source를 조회한다 (Webhook 처리용)."""
    result = await db.execute(
        select(DataSource).where(
            DataSource.provider == _PROVIDER,
            DataSource.external_id == str(strava_athlete_id),
        )
    )
    return result.scalar_one_or_none()
