"""Common exceptions for all domains."""

from typing import Any, Dict, Optional


class DomainException(Exception):
    """Base exception for all domain-specific exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize domain exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(DomainException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any = None):
        """
        Initialize not found error.

        Args:
            resource: Type of resource not found
            identifier: Resource identifier (optional)
        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404)


class AlreadyExistsError(DomainException):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, resource: str, field: str, value: Any):
        """
        Initialize already exists error.

        Args:
            resource: Type of resource
            field: Field that conflicts
            value: Value that already exists
        """
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message, status_code=400)


class ValidationError(DomainException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.

        Args:
            message: Validation error message
            field: Field that failed validation (optional)
        """
        details = {}
        if field:
            details["field"] = field
        super().__init__(message, status_code=400, details=details)


class PermissionDeniedError(DomainException):
    """Raised when user lacks required permissions."""

    def __init__(self, action: str, resource: Optional[str] = None):
        """
        Initialize permission denied error.

        Args:
            action: Action that was denied
            resource: Resource the action was attempted on (optional)
        """
        message = f"Permission denied: cannot {action}"
        if resource:
            message = f"Permission denied: cannot {action} {resource}"
        super().__init__(message, status_code=403)


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, rule: Optional[str] = None):
        """
        Initialize business rule violation error.

        Args:
            message: Error message describing the violation
            rule: Name of the business rule violated (optional)
        """
        details = {}
        if rule:
            details["rule"] = rule
        super().__init__(message, status_code=400, details=details)


class ConflictError(DomainException):
    """Raised when an operation conflicts with current state."""

    def __init__(self, message: str, resource: Optional[str] = None):
        """
        Initialize conflict error.

        Args:
            message: Error message describing the conflict
            resource: Resource involved in the conflict (optional)
        """
        details = {}
        if resource:
            details["resource"] = resource
        super().__init__(message, status_code=409, details=details)
