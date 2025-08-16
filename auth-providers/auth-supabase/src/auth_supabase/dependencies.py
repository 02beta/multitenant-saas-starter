"""Convenience exports for application dependency injection.

Import from this module in apps as:

    from auth_supabase.dependencies import create_supabase_provider, settings
"""

from . import create_supabase_provider, settings
from .provider import SupabaseAuthProvider

__all__ = [
    "create_supabase_provider",
    "settings",
    "SupabaseAuthProvider",
]
