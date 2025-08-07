"""Core settings for the application."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config: SettingsConfigDict = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        str_strip_whitespace=True,
        # env_prefix="02BETA_",
        env_ignore_empty=True,
        env_nested_delimiter=".",
        env_nested_max_split=10,
        env_parse_none_str="",
        env_parse_enums=True,
    )

    database_url: str = Field(
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        description="Synchronous database connection URL",
    )
    database_async_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres",
        description="Asynchronous database connection URL",
    )


# Global settings instance
settings = Settings()
