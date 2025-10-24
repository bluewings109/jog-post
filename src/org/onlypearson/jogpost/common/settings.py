from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    # database
    db_url: str

    # cloudinary
    cloudinary_url: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    # google maps
    google_maps_api_key: str

    # instagram
    instagram_app_name: str
    instagram_app_id: int
    instagram_app_secret: int

    model_config = SettingsConfigDict(
        env_file=None, # main에서 load_dotenv() 로 파일내용은 이미 환경변수로 로드됨
    )

settings: BaseSettings = Settings()
