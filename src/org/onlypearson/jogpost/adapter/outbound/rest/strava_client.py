import httpx

from org.onlypearson.jogpost.exception.error_code import ErrorCode
from org.onlypearson.jogpost.exception.custom_exception import StravaException
from org.onlypearson.jogpost.schema.strava_api_dto import StravaActivityResponse
from org.onlypearson.jogpost.schema.strava_api_dto import StravaTokenRefreshResponse


class StravaClient:
    async def get_header(self, access_token: str) -> dict:
        return {"Authorization": f"Bearer {access_token}"}

    async def refresh_access_token(
        self,
        client_id: int,
        client_secret: str,
        refresh_token: str
    ) -> StravaTokenRefreshResponse:

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://www.strava.com/api/v3/oauth/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    }
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.STRAVA_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                raise StravaException(ErrorCode.STRAVA_TOKEN_ERROR_1.value)

            data: dict = response.json()
            return StravaTokenRefreshResponse(**data)

    async def get_activity(
        self,
        activity_id: int,
        access_token: str
    ) -> StravaActivityResponse:
        header: dict = await self.get_header(access_token)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://www.strava.com/api/v3/activities/{activity_id}",
                    headers=header,
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.STRAVA_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                raise StravaException(ErrorCode.STRAVA_ACTIVITY_ERROR_1.value)

            data: dict = response.json()
            return StravaActivityResponse(**data)

