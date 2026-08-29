from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./recovery_agent.db"

    # Razorpay
    razorpay_key_id: str = "rzp_test_dummy_key"
    razorpay_key_secret: str = "dummy_secret"
    razorpay_webhook_secret: str = "dummy_webhook_secret"

    # Gemini
    gemini_api_key: str = "dummy_gemini_key"

    # App
    environment: str = "development"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
