import httpx

from org.onlypearson.jogpost.exception.error_code import ErrorCode
from org.onlypearson.jogpost.exception.custom_exception import StravaException
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramContainerStatusResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramCreateContainerResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramLongLivedTokenResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramPublishContainerResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramShortLivedTokenResponse


class InstagramClient:
    async def get_header(self, access_token: str) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

    async def get_short_lived_access_token_by_code(self, client_id: int, client_secret: str, redirect_uri: str, code: str) -> InstagramShortLivedTokenResponse:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.instagram.com/oauth/access_token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri,
                        "code": code,
                    }
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.INSTAGRAM_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                print(f"text={response.text}")
                raise StravaException(ErrorCode.INSTAGRAM_TOKEN_ERROR_1.value)

            data: dict = response.json()
            return InstagramShortLivedTokenResponse(**data)


    async def get_long_lived_token_by_short_lived_token(
        self,
        client_secret: str,
        short_lived_token: str
    ) -> InstagramLongLivedTokenResponse:

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://graph.instagram.com/access_token",
                    params={
                        "grant_type": "ig_exchange_token",
                        "client_secret": client_secret,
                        "access_token": short_lived_token,
                    }
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.INSTAGRAM_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                print(f"text={response.text}")
                raise StravaException(ErrorCode.INSTAGRAM_TOKEN_ERROR_2.value)

            data: dict = response.json()
            return InstagramLongLivedTokenResponse(**data)

    async def refresh_long_lived_token(
        self,
        long_lived_access_token: str
    ) -> InstagramLongLivedTokenResponse:

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://graph.instagram.com/refresh_access_token",
                    params={
                        "grant_type": "ig_refresh_token",
                        "access_token": long_lived_access_token,
                    },
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.INSTAGRAM_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                print(f"text={response.text}")
                raise StravaException(ErrorCode.INSTAGRAM_TOKEN_ERROR_3.value)

            data: dict = response.json()
            return InstagramLongLivedTokenResponse(**data)

    async def create_container(self, image_url: str, caption: str, access_token: str, instagram_user_id: int) -> InstagramCreateContainerResponse:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://graph.instagram.com/v24.0/{instagram_user_id}/media",
                    headers=await self.get_header(access_token),
                    json={
                        "image_url": image_url,
                        "caption": caption
                    },
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.INSTAGRAM_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                print(f"text={response.text}")
                raise StravaException(ErrorCode.INSTAGRAM_TOKEN_ERROR_4.value)

            data: dict = response.json()
            return InstagramCreateContainerResponse(**data)

    async def publish_container(self, container_id: str, access_token: str, instagram_user_id: int) -> InstagramPublishContainerResponse:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://graph.instagram.com/v24.0/{instagram_user_id}/media_publish",
                    headers=await self.get_header(access_token),
                    json={
                        "creation_id": container_id,
                    },
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.INSTAGRAM_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                print(f"text={response.text}")
                raise StravaException(ErrorCode.INSTAGRAM_TOKEN_ERROR_5.value)

            data: dict = response.json()
            return InstagramPublishContainerResponse(**data)

    async def get_container_status(self, container_id: str, access_token: str)->InstagramContainerStatusResponse:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://graph.instagram.com/v24.0/{container_id}",
                    params={
                        "fields": "status_code",
                        "access_token": access_token,
                    },
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.INSTAGRAM_COMMON_ERROR_1.value) from e

            if 400 <= response.status_code < 600:
                print(f"text={response.text}")
                raise StravaException(ErrorCode.INSTAGRAM_TOKEN_ERROR_6.value)

            data: dict = response.json()
            return InstagramContainerStatusResponse(**data)
