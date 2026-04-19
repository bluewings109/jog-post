from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.user import DataSourceResponse, MeResponse
from app.services import google_auth, strava_auth

router = APIRouter(prefix="/auth", tags=["auth"])

# 쿠키 이름
_JWT_COOKIE = "access_token"
_OAUTH_STATE_COOKIE = "oauth_state"

_COOKIE_OPTS = {
    "httponly": True,
    "samesite": "lax",
    "secure": False,      # 배포 시 True로 변경
}


def _google_redirect_uri(request: Request) -> str:
    return str(request.base_url) + "api/v1/auth/google/callback"


def _strava_redirect_uri(request: Request) -> str:
    return str(request.base_url) + "api/v1/auth/strava/callback"


# ────────────────────────────────────────────────────────────
# Google OAuth (로그인/인증)
# ────────────────────────────────────────────────────────────

@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    """Google OAuth 인증 페이지로 리디렉트한다."""
    redirect_uri = _google_redirect_uri(request)
    url, state = google_auth.build_login_url(redirect_uri)
    response = RedirectResponse(url)
    response.set_cookie(_OAUTH_STATE_COOKIE, state, max_age=600, **_COOKIE_OPTS)
    return response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    oauth_state: str | None = Cookie(default=None),
) -> RedirectResponse:
    """Google OAuth 콜백: code → token → 사용자 upsert → JWT 쿠키 발급."""
    if oauth_state is None or oauth_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    try:
        token_data = await google_auth.exchange_code(code, _google_redirect_uri(request))
        user_info = await google_auth.get_user_info(token_data["access_token"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Google OAuth failed"
        )

    google_id = user_info["sub"]
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_id=google_id,
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.email = user_info["email"]
        user.name = user_info.get("name")
        user.picture = user_info.get("picture")
        await db.commit()

    jwt = create_access_token(user.id)
    redirect = RedirectResponse(url=settings.FRONTEND_URL + "/activities")
    redirect.set_cookie(_JWT_COOKIE, jwt, max_age=settings.JWT_EXPIRE_MINUTES * 60, **_COOKIE_OPTS)
    redirect.delete_cookie(_OAUTH_STATE_COOKIE)
    return redirect


@router.post("/logout")
async def logout(response: Response) -> dict:
    """JWT 쿠키를 삭제한다."""
    response.delete_cookie(_JWT_COOKIE)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """현재 로그인 사용자 정보와 연동된 데이터 소스 목록을 반환한다."""
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == current_user.id)
    )
    sources = result.scalars().all()
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        data_sources=[DataSourceResponse.model_validate(s) for s in sources],
    )


# ────────────────────────────────────────────────────────────
# Strava OAuth (데이터 연동)
# ────────────────────────────────────────────────────────────

@router.get("/strava/connect")
async def strava_connect(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> RedirectResponse:
    """Strava 데이터 연동 OAuth 페이지로 리디렉트한다."""
    url, state = strava_auth.build_connect_url(_strava_redirect_uri(request))
    response = RedirectResponse(url)
    response.set_cookie(_OAUTH_STATE_COOKIE, state, max_age=600, **_COOKIE_OPTS)
    return response


@router.get("/strava/callback")
async def strava_callback(
    code: str,
    state: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    oauth_state: str | None = Cookie(default=None),
) -> RedirectResponse:
    """Strava OAuth 콜백: code → token → data_sources upsert."""
    if oauth_state is None or oauth_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    try:
        token_data = await strava_auth.exchange_code(code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Strava OAuth failed"
        )

    await strava_auth.upsert_data_source(current_user.id, token_data, db)

    redirect = RedirectResponse(url=settings.FRONTEND_URL + "/activities")
    redirect.delete_cookie(_OAUTH_STATE_COOKIE)
    return redirect


@router.delete("/strava/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def strava_disconnect(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Strava 데이터 연동을 해제한다."""
    result = await db.execute(
        select(DataSource).where(
            DataSource.user_id == current_user.id,
            DataSource.provider == "strava",
        )
    )
    data_source = result.scalar_one_or_none()
    if data_source:
        await db.delete(data_source)
        await db.commit()
