"""Core common package."""

from .exceptions import (
    AlreadyExistsError,
    BusinessRuleViolationError,
    ConflictError,
    DomainException,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from .mixins import AuditFieldsMixin, SoftDeleteMixin

__all__ = [
    # Base
    "Base",
    # Exceptions
    "AlreadyExistsError",
    "BusinessRuleViolationError",
    "ConflictError",
    "DomainException",
    "NotFoundError",
    "PermissionDeniedError",
    "ValidationError",
    # Mixins
    "AuditFieldsMixin",
    "SoftDeleteMixin",
]
