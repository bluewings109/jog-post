from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://jogpost:jogpost@localhost:5432/jogpost"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7일

    # Google OAuth (로그인/인증)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Strava OAuth (데이터 연동)
    STRAVA_CLIENT_ID: str = ""
    STRAVA_CLIENT_SECRET: str = ""
    STRAVA_WEBHOOK_VERIFY_TOKEN: str = "jog-post-webhook"

    # LLM (공급자 미결정 — 나중에 설정)
    LLM_PROVIDER: str = ""  # openai | anthropic | ollama
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    # App
    FRONTEND_URL: str = "http://localhost:5173"


settings = Settings()
