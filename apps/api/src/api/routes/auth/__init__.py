"""Authentication routes package (dependencies only)."""

from .dependencies import get_current_token, get_current_user

__all__ = ["get_current_token", "get_current_user"]
