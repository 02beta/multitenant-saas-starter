"""Application settings configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings"]


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        str_strip_whitespace=True,
    )

    # Debug settings
    debug: bool = Field(default=False, description="Enable debug mode")

    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
        ],
        description="Allowed CORS origins",
    )
    api_version: str = Field(default="0.0.0", description="API version")
    api_title: str = Field(default="Multi-tenant SaaS API", description="API title")
    api_description: str = Field(
        default="API for the Multi-tenant SaaS application",
        description="API description",
    )

    # Supabase settings
    supabase_api_url: str = Field(default="", description="Supabase API URL")
    supabase_public_key: str = Field(default="", description="Supabase anonymous key")
    supabase_secret_key: str = Field(
        default="", description="Supabase service role key"
    )
    auth_jwt_secret: str = Field(default="", description="Supabase JWT secret")


# Global settings instance
settings = Settings()
