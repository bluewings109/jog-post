from io import BytesIO

import httpx
from PIL import Image
from PIL.ImageFile import ImageFile

from org.onlypearson.jogpost.common.settings import settings
from org.onlypearson.jogpost.exception.custom_exception import StravaException
from org.onlypearson.jogpost.exception.error_code import ErrorCode


class GoogleClient:
    async def get_header(self, access_token: str) -> dict:
        return {"Authorization": f"Bearer {access_token}"}

    async def get_static_map_images_with_path(
        self,
        lat_center: float,
        lng_center: float,
        encoded_polyline: str,
        map_width_px: int,
        map_height_px: int,
        zoom: int,

    ) -> ImageFile:

        query_params: dict = {
            "center": f"{lat_center},{lng_center}",
            "zoom": zoom,
            "size": f"{map_width_px}x{map_height_px}",
            "format": "png",
            "region": "kr",
            "path": f"weight:5|color:red|enc:{encoded_polyline}",
            "style": "element:labels|visibility:off",
            "key": settings.google_maps_api_key
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://maps.googleapis.com/maps/api/staticmap",
                    params=query_params,
                )

            except httpx.HTTPError as e:
                raise StravaException(ErrorCode.GOOGLE_COMMON_ERROR_1.value) from e

            if 400<= response.status_code < 600:
                raise StravaException(ErrorCode.GOOGLE_MAPS_ERROR_1.value)

            static_map_image: ImageFile = Image.open(BytesIO(response.content))
            return static_map_image

