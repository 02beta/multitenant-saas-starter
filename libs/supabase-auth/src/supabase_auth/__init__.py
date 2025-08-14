"""Supabase authentication provider."""

from core.domains.auth.factory import AuthProviderRegistry

from .config import SupabaseConfig
from .provider import SupabaseAuthProvider


def create_supabase_provider(config: dict) -> SupabaseAuthProvider:
    """Factory function for Supabase provider."""
    supabase_config = SupabaseConfig(**config)
    return SupabaseAuthProvider(supabase_config)


# Auto-register the provider when this package is imported
AuthProviderRegistry.register_provider("supabase", create_supabase_provider)

__all__ = [
    "SupabaseAuthProvider",
    "SupabaseConfig",
    "create_supabase_provider",
]
