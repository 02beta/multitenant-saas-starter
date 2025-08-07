"""Supabase-specific configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SupabaseConfig(BaseSettings):
    """Supabase authentication configuration."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    # Authentication configuration
    auth_provider: str = Field(
        default="supabase",
        description="Authentication provider to use (supabase, auth0, clerk, custom)",
    )

    # Supabase configuration
    supabase_api_url: str = Field(
        default="",
        description="Supabase API URL",
    )
    auth_jwt_secret: str = Field(
        default="",
        description="Supabase JWT secret for token validation",
    )
    supabase_public_key: str = Field(
        default="",
        description="Supabase anonymous key",
    )
    supabase_secret_key: str = Field(
        default="",
        description="Supabase service role key",
    )
