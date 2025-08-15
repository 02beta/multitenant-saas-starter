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
        description="Authentication provider is set to `supabase` do not change this "
        "value if using supabase as the auth provider.",
    )

    # Supabase configuration
    supabase_api_url: str = Field(
        default="http://localhost:54321",
        description="Supabase API URL, defaults to the local supabase api url",
    )
    auth_jwt_secret: str = Field(
        default="super-secret-jwt-token-with-at-least-32-characters",
        description="Supabase JWT secret for token validation, defaults to supabase "
        "local default value",
    )
    supabase_public_key: str = Field(
        description="Supabase publishable key (new version of anon key), "
        "defaults to supabase local default value for public anon key.",
    )
    supabase_secret_key: str = Field(
        description="Supabase secret key (new version of service role key), "
        "defaults to supabase local default value for secret key.",
    )


settings = SupabaseConfig()
