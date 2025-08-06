"""Application settings configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings", "Settings"]


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Debug settings
    debug: bool = Field(default=False, description="Enable debug mode")

    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # Database settings
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        description="Database connection URL",
    )

    # Supabase settings
    supabase_url: str = Field(default="", description="Supabase API URL")
    supabase_anon_key: str = Field(default="", description="Supabase anonymous key")
    supabase_service_role_key: str = Field(
        default="", description="Supabase service role key"
    )
    supabase_jwt_secret: str = Field(default="", description="Supabase JWT secret")


# Global settings instance
settings = Settings()
