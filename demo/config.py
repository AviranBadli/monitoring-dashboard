from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    THANOS_URL: str = "http://localhost:9091"
    THANOS_TOKEN: str = ""
    TEST_ROW: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
