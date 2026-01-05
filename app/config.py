from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/bitly"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
    )


settings = Settings()
