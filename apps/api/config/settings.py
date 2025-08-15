"""Application settings configuration."""

import json
from importlib.metadata import version
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings"]


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        str_strip_whitespace=True,
        env_ignore_empty=True,
        arbitrary_types_allowed=True,
    )
    # Debug settings
    debug: bool = Field(default=False, description="Enable debug mode")
    # API settings
    api_cors_origins: list[str] = Field(
        default=[
            "https://02beta.com",  # allow 02beta.com
            "https://*.02beta.com",  # allow subdomains on 02beta.com
            "https://*.vercel.app",  # allow vercel app
            "https://*.fly.dev",  # allow fly.dev app
            "http://localhost:3000",  # allow localhost for web app
            "http://localhost:3001",  # allow localhost for admin app
            "http://localhost:3002",  # allow localhost for docs app
            "http://localhost:3003",  # allow localhost for marketing website
        ],
        description="Allowed CORS origins by default includes "
        "localhost ports 3000-3003, "
        "02beta.com subdomains and any vercel or fly.dev app",
        validation_alias="API_CORS_ORIGINS_JSON",
    )

    # Raw env input to bypass pydantic-settings JSON decoding
    api_cors_origins_raw: str | None = Field(
        default=None,
        validation_alias="API_CORS_ORIGINS",
        description=(
            "Raw env for CORS origins. Accepts JSON array or comma-separated"
            " string. Prefer JSON in production."
        ),
    )

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def _coerce_cors_origins(cls, value: Any) -> list[str]:
        """Allow JSON array or comma-separated string for CORS origins.

        - If JSON parsing fails, fall back to comma-splitting.
        - Filters out empty entries.
        """
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [
                        item.strip()
                        for item in parsed
                        if isinstance(item, str) and item.strip()
                    ]
            except Exception:
                pass
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def _apply_raw_cors_origins(self) -> "Settings":
        """If raw env is provided, parse it and assign to api_cors_origins."""
        if self.api_cors_origins_raw:
            text = self.api_cors_origins_raw.strip()
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    self.api_cors_origins = [
                        item.strip()
                        for item in parsed
                        if isinstance(item, str) and item.strip()
                    ]
                    return self
            except Exception:
                self.api_cors_origins = [
                    part.strip() for part in text.split(",") if part.strip()
                ]
        return self

    api_version: str = Field(
        default_factory=lambda: version("api"),
        description="API version as it displays in the docs. "
        "Default derives from the value of the version in the pyproject.toml file.",
    )
    api_title: str = Field(
        default="API for Multitenant SaaS Starter",
        description="API title as it displays in the docs.",
    )
    api_description: str = Field(
        default="API for the Multitenant SaaS Starter",
        description="API description as it displays in the docs.",
    )
    # Supabase settings required for using supabase as the auth provider
    supabase_api_url: str = Field(
        default="",
        description="Supabase API URL. This is used to connect to the supabase database.",
    )
    supabase_public_key: str = Field(
        default="",
        description="Supabase publishable api key. Formerly the supabase anon key.",
    )
    supabase_secret_key: str = Field(
        default="",
        description="Supabase secret api key. Formerly the supabase service role key.",
    )
    auth_jwt_secret: str = Field(
        default="",
        description="JWT secret for the auth provider. This is used to sign the JWT tokens for the auth provider.",
    )
    auth_provider: str = Field(
        default="supabase",
        description="Auth provider. Default is supabase, but can be changed to any other provider "
        "configured in a library package that implements the auth provider interface provided in the "
        "`core` package. See the `core` and `supabase-auth` library packages in the `libs` directory for more details.",
    )


# Global settings instance
settings = Settings()
