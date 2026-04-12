import secrets
from urllib.parse import urlencode

import httpx

from app.core.config import settings

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_SCOPES = "openid email profile"


def build_login_url(redirect_uri: str) -> tuple[str, str]:
    """Google OAuth 인증 URL과 state 값을 반환한다."""
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}", state


async def exchange_code(code: str, redirect_uri: str) -> dict:
    """Authorization code를 access_token으로 교환한다."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_user_info(access_token: str) -> dict:
    """Google access_token으로 사용자 프로필 정보를 조회한다.

    반환 필드: sub (google_id), email, name, picture
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
