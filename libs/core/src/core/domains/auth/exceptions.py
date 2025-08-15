"""Authentication-specific exceptions."""

from core.common.exceptions import DomainException


class AuthenticationError(DomainException):
    """Base authentication error."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username/password."""

    def __init__(self):
        super().__init__("Invalid credentials provided")


class TokenExpiredError(AuthenticationError):
    """Access token has expired."""

    def __init__(self):
        super().__init__("Authentication token has expired")


class InvalidTokenError(AuthenticationError):
    """Invalid or malformed token."""

    def __init__(self):
        super().__init__("Invalid authentication token")


class UserNotFoundError(AuthenticationError):
    """User not found in auth provider."""

    def __init__(self, user_identifier: str):
        super().__init__(f"User not found: {user_identifier}")


class UnsupportedAuthProviderError(AuthenticationError):
    """Unsupported authentication provider."""

    def __init__(self, provider: str):
        super().__init__(f"Unsupported authentication provider: {provider}")


class SessionNotFoundError(AuthenticationError):
    """Session not found or expired."""

    def __init__(self):
        super().__init__("Authentication session not found or expired")


class OrganizationAccessDeniedError(AuthenticationError):
    """User does not have access to the requested organization."""

    def __init__(self, organization_id: str):
        super().__init__(f"Access denied to organization: {organization_id}")
