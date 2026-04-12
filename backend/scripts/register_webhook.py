"""Strava 웹훅 구독 등록 스크립트 (일회성 실행).

사용법:
    uv run python scripts/register_webhook.py --callback-url https://your-domain.com/api/v1/webhook/strava

로컬 개발 시:
    1. ngrok을 실행한다: ngrok http 8000
    2. ngrok이 출력한 HTTPS URL을 --callback-url에 지정한다
       예: uv run python scripts/register_webhook.py --callback-url https://abc123.ngrok.io/api/v1/webhook/strava

환경 변수 필요:
    STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_WEBHOOK_VERIFY_TOKEN
"""

import argparse
import asyncio

import httpx

from app.core.config import settings

_STRAVA_SUBSCRIPTION_URL = "https://www.strava.com/api/v3/push_subscriptions"


async def list_subscriptions() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _STRAVA_SUBSCRIPTION_URL,
            params={
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def delete_subscription(subscription_id: int) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{_STRAVA_SUBSCRIPTION_URL}/{subscription_id}",
            params={
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()


async def create_subscription(callback_url: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _STRAVA_SUBSCRIPTION_URL,
            data={
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
                "callback_url": callback_url,
                "verify_token": settings.STRAVA_WEBHOOK_VERIFY_TOKEN,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def main(callback_url: str, force: bool) -> None:
    print("현재 Strava 웹훅 구독 조회 중...")
    existing = await list_subscriptions()

    if existing:
        print(f"기존 구독 발견: {existing}")
        if not force:
            print("기존 구독이 있습니다. --force 옵션으로 덮어쓸 수 있습니다.")
            return
        for sub in existing:
            await delete_subscription(sub["id"])
            print(f"구독 삭제: id={sub['id']}")

    print(f"웹훅 구독 등록 중: {callback_url}")
    result = await create_subscription(callback_url)
    print(f"구독 등록 완료: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strava 웹훅 구독 등록")
    parser.add_argument("--callback-url", required=True, help="웹훅 수신 URL (HTTPS)")
    parser.add_argument("--force", action="store_true", help="기존 구독 삭제 후 재등록")
    args = parser.parse_args()

    asyncio.run(main(args.callback_url, args.force))
