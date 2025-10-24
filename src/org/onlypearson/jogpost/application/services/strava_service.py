import math
from datetime import datetime
from zoneinfo import ZoneInfo

import polyline
from PIL.ImageFile import ImageFile
from sqlalchemy.ext.asyncio import AsyncSession

from org.onlypearson.jogpost.adapter.outbound.cloudinary.cloudinary_client import CloudinaryClient
from org.onlypearson.jogpost.adapter.outbound.repository.activity_repository import ActivityRepository
from org.onlypearson.jogpost.adapter.outbound.repository.athlete_repository import AthleteRepository
from org.onlypearson.jogpost.adapter.outbound.repository.orm.activity import Activity
from org.onlypearson.jogpost.adapter.outbound.rest.google_client import GoogleClient
from org.onlypearson.jogpost.adapter.outbound.rest.strava_client import StravaClient
from org.onlypearson.jogpost.application.services.instagram_service import InstagramService
from org.onlypearson.jogpost.common.constants import ActivityType
from org.onlypearson.jogpost.common.constants import ObjectType
from org.onlypearson.jogpost.common.logger_support import get_logger
from org.onlypearson.jogpost.database.session import session_context
from org.onlypearson.jogpost.domain.model.activity_domain import ActivityDomain
from org.onlypearson.jogpost.domain.model.athlete_domain import AthleteDomain
from org.onlypearson.jogpost.exception.custom_exception import StravaException
from org.onlypearson.jogpost.exception.error_code import ErrorCode
from org.onlypearson.jogpost.schema.strava_api_dto import StravaActivityMapDto
from org.onlypearson.jogpost.schema.strava_api_dto import StravaActivityResponse
from org.onlypearson.jogpost.schema.strava_api_dto import StravaTokenRefreshResponse
from org.onlypearson.jogpost.schema.strava_api_dto import StravaWebhookRequest


class StravaService:
    def __init__(
        self,
        athlete_repository: AthleteRepository,
        activity_repository: ActivityRepository,
        strava_client: StravaClient,
        google_client: GoogleClient,
        cloudinary_client: CloudinaryClient,
        instagram_service: InstagramService,
    ):
        self._athlete_repository = athlete_repository
        self._strava_client = strava_client
        self._google_client = google_client
        self._cloudinary_client = cloudinary_client
        self._instagram_service = instagram_service
        self._activity_repository = activity_repository
        self._logger = get_logger(__name__)

    async def process_webhook_event(
        self,
        request: StravaWebhookRequest,
    ):
        print(f"request: {request.model_dump()}")
        self._logger.info(f"request: {request.model_dump()}")
        if request.object_type != ObjectType.ACTIVITY:
            # ACTIVITY 이벤트가 아닌 경우 로그만 남기고 종료
            self._logger.info(f"object_type: [{request.object_type}]. Do nothing..")
            return

        athlete_id: int = request.owner_id
        activity_id: int = request.object_id

        async with session_context() as session:
            await self.process_activity_event(activity_id, athlete_id, session)

    async def process_activity_event(self, activity_id: int, athlete_id: int, session: AsyncSession, is_test: bool = False):
        access_token: str = await self.ensure_access_token(athlete_id, session)
        response: StravaActivityResponse = await self._strava_client.get_activity(activity_id, access_token)
        if response.type == ActivityType.RUN:
            activity_domain: ActivityDomain = ActivityDomain(
                activity_id=activity_id,
                athlete_id=athlete_id,
                name=response.name,
                distance=response.distance,
                elapsed_time=response.elapsed_time,
                type=response.type,
                start_date=response.start_date,
                average_heartrate=response.average_heartrate,
                max_heartrate=response.max_heartrate,
                polyline=response.map.polyline,
                summary_polyline=response.map.summary_polyline,
            )
            await self.save_activity(activity_domain, session)
            route_image: ImageFile = await self.create_route_image(activity_domain.polyline)
            route_image.filename = await self.create_route_image_filename_without_ext()
            if is_test:
                route_image.show()
            else:
                image_url: str = self._cloudinary_client.upload_image(route_image)
                print(f"image_url: {image_url}")
                caption: str = await self._make_image_caption(response.start_date, response.distance, response.elapsed_time)
                media_id: str = await self._instagram_service.upload_image(athlete_id, image_url, caption, session)
                print(f"media_id: {media_id}")
                await self._activity_repository.update_is_posted(activity_id, True, session)

    async def create_route_image_filename_without_ext(self) -> str:
        now_string: str = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d%H%M%S")
        return now_string

    async def create_route_image(self, encoded_polyline: str | None) -> ImageFile:

        if not encoded_polyline:
            # polyline이 없는 경우도 로그 남기고 종료
            print("There is no polyline")
            raise StravaException(ErrorCode.STRAVA_ACTIVITY_ERROR_2.value, "The activity does not contain polyline!")

        coordinates: list[tuple[float, float]] = polyline.decode(encoded_polyline)
        lats: list[float] = [lat for lat, lng in coordinates]
        lngs: list[float] = [lng for lat, lng in coordinates]
        lat_min = min(lats)
        lat_max = max(lats)
        lat_center: float = (lat_min + lat_max) / 2
        lng_min = min(lngs)
        lng_max = max(lngs)
        lng_center: float = (lng_min + lng_max) / 2

        map_width_px: int = 800
        map_height_px: int = 1000
        zoom: int = self.get_optimal_zoom(lat_min, lat_max, lng_min, lng_max, map_width_px, map_height_px)

        route_image: ImageFile = await self._google_client.get_static_map_images_with_path(
            lat_center, lng_center, encoded_polyline,
            map_width_px,map_height_px, zoom)
        return route_image

    async def ensure_access_token(self, athlete_id: int, session: AsyncSession) -> str:
        domain: AthleteDomain = await self._athlete_repository.select_by_id(athlete_id, session)
        now_timestamp: int = int(datetime.now().timestamp())

        if now_timestamp-60 < domain.expire_date:
            print("Skip refreshing token...")
            self._logger.info("Skip refreshing token...")
            return domain.access_token

        # 만료 1분 전 refresh
        print("Refreshing token...")
        self._logger.info("Refreshing token...")
        token_response: StravaTokenRefreshResponse = await self._strava_client.refresh_access_token(91743, "14782eebdd9a6c2efaca7e84f1d80da378c82ccb", "b7291d1bbbcf91e1ec8fe6ca01b75c394195a485")
        await self._athlete_repository.update_athlete_token(athlete_id, token_response.access_token, token_response.refresh_token, token_response.expires_at, session)
        print("Refreshing token completed!")
        self._logger.info("Refreshing token completed!")
        return token_response.access_token


    def lat_to_pixel(self, lat: float, zoom: int) -> float:
        siny = math.sin(lat * math.pi / 180)
        y = 0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)
        return y * 256 * 2 ** zoom

    def lng_to_pixel(self, lng: float, zoom: int) -> float:
        x = (lng + 180) / 360
        return x * 256 * 2 ** zoom

    def get_optimal_zoom(self, min_lat, max_lat, min_lng, max_lng, map_width_px=640, map_height_px=640):
        for z in reversed(range(0, 21)):  # Google Maps zoom range: 0~21
            lat_diff_px = abs(self.lat_to_pixel(max_lat, z) - self.lat_to_pixel(min_lat, z))
            lng_diff_px = abs(self.lng_to_pixel(max_lng, z) - self.lng_to_pixel(min_lng, z))
            if lat_diff_px <= map_height_px and lng_diff_px <= map_width_px:
                return z-1
        return 0

    async def _make_image_caption(self, start_date: datetime, distance: float, elapsed_time: float)-> str:
        # 날짜 포맷 (예: 2025. 10. 12.)
        date_str = start_date.strftime("%Y. %m. %d.")

        # 거리 (미터 → km, 소수점 1자리)
        km = round(distance / 1000, 1)

        # 시간 포맷 (초 → 분, 초)
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        # 문자열 조합
        caption = f"{date_str} / {km}km / {minutes}분 {seconds:02d}초\nposted by jog-post for onlypearson"

        return caption

    async def save_activity(self, activity_domain: ActivityDomain, session: AsyncSession):
        check_domain: ActivityDomain|None = await self._activity_repository.select_by_id_with_no_raise(activity_domain.activity_id, session)

        if check_domain is None:
            # 저장이 되어 있지 않으면 저장
            await self._activity_repository.insert_activity(activity_domain, session)
