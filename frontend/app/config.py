from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    BACKEND_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()
