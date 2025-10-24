import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from org.onlypearson.jogpost.adapter.outbound.repository.athlete_repository import AthleteRepository
from org.onlypearson.jogpost.adapter.outbound.rest.instagram_client import InstagramClient
from org.onlypearson.jogpost.common.logger_support import get_logger
from org.onlypearson.jogpost.domain.model.athlete_domain import AthleteDomain
from org.onlypearson.jogpost.exception.custom_exception import InstagramException
from org.onlypearson.jogpost.exception.error_code import ErrorCode
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramContainerStatusResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramCreateContainerResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramLongLivedTokenResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramPublishContainerResponse
from org.onlypearson.jogpost.schema.instragram_api_dto import InstagramShortLivedTokenResponse
from org.onlypearson.jogpost.common.constants import InstagramContainerStatus
from org.onlypearson.jogpost.common.settings import settings


class InstagramService:
    def __init__(
        self,
        athlete_repository: AthleteRepository,
        instagram_client: InstagramClient,
    ):
        self._athlete_repository = athlete_repository
        self._instagram_client = instagram_client
        self._logger = get_logger(__name__)

    async def initial_verify(self, athlete_id: int, redirect_uri: str, code: str, session: AsyncSession) -> str:
        client_id: int = settings.instagram_app_id
        client_secret: str = settings.instagram_app_secret

        short_lived_token_response: InstagramShortLivedTokenResponse = await self._instagram_client.get_short_lived_access_token_by_code(client_id, client_secret, redirect_uri, code)
        short_lived_token: str = short_lived_token_response.access_token
        instagram_user_id: int = short_lived_token_response.user_id

        long_lived_token_response: InstagramLongLivedTokenResponse = await self._instagram_client.get_long_lived_token_by_short_lived_token(client_secret, short_lived_token)
        long_lived_token: str = long_lived_token_response.access_token
        expires_in: int = long_lived_token_response.expires_in
        now_timestamp: int = int(datetime.now().timestamp())
        expire_date = now_timestamp + expires_in

        await self._athlete_repository.update_instagram_token(athlete_id, long_lived_token, expire_date, instagram_user_id, session)
        return long_lived_token

    async def ensure_access_token(self, athlete_id: int, session: AsyncSession) -> str:
        domain: AthleteDomain = await self._athlete_repository.select_by_id(athlete_id, session)
        now_timestamp: int = int(datetime.now().timestamp())

        if now_timestamp-60 < domain.instagram_expire_date:
            print("Skip refreshing instagram token...")
            self._logger.info("Skip refreshing instagram token...")
            return domain.instagram_access_token

        # 만료 1분 전 refresh
        print("Refreshing Instagram token...")
        self._logger.info("Refreshing Instagram token...")
        token_response: InstagramLongLivedTokenResponse = await self._instagram_client.refresh_long_lived_token(domain.instagram_access_token)
        now_timestamp: int = int(datetime.now().timestamp())
        expire_date = now_timestamp + token_response.expires_in
        await self._athlete_repository.update_instagram_token(athlete_id, token_response.access_token, expire_date, session)
        print("Refreshing instagram token completed!")
        self._logger.info("Refreshing instagram token completed!")
        return token_response.access_token

    async def _create_container(self, athlete_id: int, image_url: str, caption: str, session: AsyncSession) -> str:
        access_token: str = await self.ensure_access_token(athlete_id, session)
        instagram_user_id: int = await self._get_instagram_user_id(athlete_id, session)
        container_response: InstagramCreateContainerResponse = await self._instagram_client.create_container(image_url, caption, access_token, instagram_user_id)
        container_id: str = container_response.id
        return container_id

    async def _publish_container(self, athlete_id: int, container_id: str, session: AsyncSession) -> str:
        access_token: str = await self.ensure_access_token(athlete_id, session)
        instagram_user_id: int = await self._get_instagram_user_id(athlete_id, session)
        publish_response: InstagramPublishContainerResponse = await self._instagram_client.publish_container(container_id, access_token, instagram_user_id)
        media_id: str = publish_response.id
        return media_id

    async def upload_image(self, athlete_id: int, image_url: str, caption: str, session: AsyncSession) -> str:
        container_id: str = await self._create_container(athlete_id, image_url,caption, session)
        await self._wait_until_ready(athlete_id, container_id, session)
        media_id: str = await self._publish_container(athlete_id, container_id, session)
        return media_id

    async def _get_instagram_user_id(self, athlete_id: int, session: AsyncSession) -> int:
        athlete_domain: AthleteDomain = await self._athlete_repository.select_by_id(athlete_id, session)
        return athlete_domain.instagram_user_id

    async def _wait_until_ready(self, athlete_id: int, container_id: str, session: AsyncSession):
        access_token: str = await self.ensure_access_token(athlete_id, session)
        try_count=0

        while(True):
            status_response: InstagramContainerStatusResponse = await self._instagram_client.get_container_status(container_id, access_token)
            status = status_response.status_code
            if status == InstagramContainerStatus.FINISHED:
                print("Instagram container status is FINISHED")
                return
            elif status == InstagramContainerStatus.ERROR:
                print("Instagram container status is ERROR")
                raise InstagramException(ErrorCode.INSTAGRAM_TOKEN_ERROR_7.value)
            else:
                if try_count>=5:
                    raise InstagramException(ErrorCode.INSTAGRAM_TOKEN_ERROR_8.value)
                print(f"Processing... current_status: {status}")
                await asyncio.sleep(3)
