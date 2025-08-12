"""Authentication provider protocols - vendor agnostic."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from .models import AuthResult, AuthUser, TokenPair


@runtime_checkable
class AuthProvider(Protocol):
    """Authentication provider protocol that all implementations must follow."""

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate user with email and password."""
        ...

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate access token and return user info."""
        ...

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token."""
        ...

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create new user in the auth provider."""
        ...

    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by provider user ID."""
        ...

    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email address."""
        ...

    async def update_user(
        self, user_id: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Update user data in the auth provider."""
        ...

    async def delete_user(self, user_id: str) -> bool:
        """Delete user from the auth provider."""
        ...

    async def logout(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """Logout user and invalidate session."""
        ...


class AuthProviderStub:
    """Stub implementation for testing or when no provider is configured."""

    async def authenticate(self, email: str, password: str) -> AuthResult:
        raise NotImplementedError("No authentication provider configured")

    async def validate_token(self, token: str) -> Dict[str, Any]:
        raise NotImplementedError("No authentication provider configured")

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        raise NotImplementedError("No authentication provider configured")

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        raise NotImplementedError("No authentication provider configured")

    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        raise NotImplementedError("No authentication provider configured")

    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        raise NotImplementedError("No authentication provider configured")

    async def update_user(
        self, user_id: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        raise NotImplementedError("No authentication provider configured")

    async def delete_user(self, user_id: str) -> bool:
        raise NotImplementedError("No authentication provider configured")

    async def logout(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        raise NotImplementedError("No authentication provider configured")
