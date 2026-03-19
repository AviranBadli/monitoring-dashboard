"""Application configuration"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # API Settings
    PROJECT_NAME: str = "GPU Monitoring API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Victoria Metrics
    VICTORIA_METRICS_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []


settings = Settings()
