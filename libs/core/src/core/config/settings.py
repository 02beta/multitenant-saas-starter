from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        description="Synchronous database connection URL",
    )
    database_async_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres",
        description="Asynchronous database connection URL",
    )
    model_config = {
        "env_file": Path(__file__).parent.parent.parent.parent.parent / ".env.local",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()
