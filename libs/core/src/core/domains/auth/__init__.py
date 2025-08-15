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
from .protocols import AuthProvider, AuthProviderStub
from .schemas import (
    AuthProviderType,
    AuthResult,
    AuthUser,
    ForgotPasswordRequest,
    LoginResponseExtended,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    TokenPair,
)
from .service import AuthService

__all__ = [
    # Protocols
    "AuthProvider",
    "AuthProviderStub",
    # Schemas
    "AuthProviderType",
    "AuthResult",
    "AuthUser",
    "TokenPair",
    "SignupRequest",
    "SignupResponse",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "LoginResponseExtended",
    # Factory
    "AuthProviderRegistry",
    # Service
    "AuthService",
    # Exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "OrganizationAccessDeniedError",
    "SessionNotFoundError",
    "TokenExpiredError",
    "UnsupportedAuthProviderError",
    "UserNotFoundError",
]
