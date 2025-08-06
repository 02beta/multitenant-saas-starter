"""User domain specific exceptions."""

from core.common.exceptions import AlreadyExistsError, NotFoundError, ValidationError

__all__ = [
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "InvalidEmailFormatError",
    "WeakPasswordError",
]


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""

    def __init__(self, user_id: str):
        """
        Initialize user not found error.

        Args:
            user_id: The user ID that was not found
        """
        super().__init__(resource="User", identifier=user_id)


class UserAlreadyExistsError(AlreadyExistsError):
    """Raised when attempting to create a user with an email that already exists."""

    def __init__(self, email: str):
        """
        Initialize user already exists error.

        Args:
            email: The email that already exists
        """
        super().__init__(resource="User", field="email", value=email)


class InvalidEmailFormatError(ValidationError):
    """Raised when an email format is invalid."""

    def __init__(self, email: str):
        """
        Initialize invalid email format error.

        Args:
            email: The invalid email
        """
        super().__init__(
            message=f"Invalid email format: {email}",
            field="email",
        )


class WeakPasswordError(ValidationError):
    """Raised when a password doesn't meet security requirements."""

    def __init__(self, reason: str):
        """
        Initialize weak password error.

        Args:
            reason: Specific reason why password is weak
        """
        super().__init__(
            message=f"Password does not meet security requirements: {reason}",
            field="password",
        )
