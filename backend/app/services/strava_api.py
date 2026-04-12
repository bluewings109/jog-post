"""Strava REST API 클라이언트.

토큰 갱신은 호출자(activity_sync)가 책임진다.
이 모듈은 순수하게 HTTP 요청/응답만 담당한다.
"""

import httpx

_BASE = "https://www.strava.com/api/v3"


async def fetch_activity(activity_id: int, access_token: str) -> dict:
    """활동 상세 정보를 조회한다 (laps 포함).

    Strava API: GET /activities/{id}?include_all_efforts=false
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_BASE}/activities/{activity_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"include_all_efforts": "false"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_athlete_activities(
    access_token: str,
    *,
    page: int = 1,
    per_page: int = 30,
    before: int | None = None,
    after: int | None = None,
) -> list[dict]:
    """선수의 활동 목록을 조회한다 (수동 동기화용).

    Strava API: GET /athlete/activities
    """
    params: dict = {"page": page, "per_page": per_page}
    if before:
        params["before"] = before
    if after:
        params["after"] = after

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_BASE}/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        resp.raise_for_status()
        return resp.json()
