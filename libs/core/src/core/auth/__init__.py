"""Core authentication module."""

from .exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    OrganizationAccessDeniedError,
    SessionNotFoundError,
    TokenExpiredError,
    UnsupportedAuthProviderError,
    UserNotFoundError,
)
from .factory import AuthProviderRegistry
from .models import (
    AuthProviderType,
    AuthResult,
    AuthSessionModel,
    AuthUser,
    AuthUserModel,
    TokenPair,
)
from .protocols import AuthProvider, AuthProviderStub
from .service import AuthService

__all__ = [
    "AuthProvider",
    "AuthProviderStub",
    "AuthProviderType",
    "AuthUser",
    "AuthResult",
    "TokenPair",
    "AuthUserModel",
    "AuthSessionModel",
    "AuthProviderRegistry",
    "AuthService",
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "UserNotFoundError",
    "UnsupportedAuthProviderError",
    "SessionNotFoundError",
    "OrganizationAccessDeniedError",
]
