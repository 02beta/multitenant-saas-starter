"""Memberships domain specific exceptions."""

from typing import Optional
from uuid import UUID

from core.common.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)

__all__ = [
    "MembershipNotFoundError",
    "InvitationNotFoundError",
    "UserAlreadyMemberError",
    "UserAlreadyInvitedError",
    "InvitationAlreadyAcceptedError",
    "InsufficientPermissionsError",
    "NotOrganizationMemberError",
    "LastOwnerRemovalError",
]


class MembershipNotFoundError(NotFoundError):
    """Raised when a membership relationship is not found."""

    def __init__(
        self, organization_id: Optional[UUID] = None, user_id: Optional[UUID] = None
    ):
        """
        Initialize membership not found error.

        Args:
            organization_id: Organization ID (optional)
            user_id: User ID (optional)
        """
        if organization_id and user_id:
            super().__init__(
                resource="User",
                identifier=f"user_id={user_id} in organization_id={organization_id}",
            )
        else:
            super().__init__(resource="Organization user relationship")


class InvitationNotFoundError(NotFoundError):
    """Raised when an invitation is not found."""

    def __init__(self):
        """Initialize invitation not found error."""
        super().__init__(resource="Invitation")


class UserAlreadyMemberError(ConflictError):
    """Raised when user is already an active member of the organization."""

    def __init__(self):
        """Initialize user already member error."""
        super().__init__(
            message="User is already an active member of this organization",
            resource="membership",
        )


class UserAlreadyInvitedError(ConflictError):
    """Raised when user has already been invited to the organization."""

    def __init__(self):
        """Initialize user already invited error."""
        super().__init__(
            message="User has already been invited to this organization",
            resource="membership",
        )


class InvitationAlreadyAcceptedError(ConflictError):
    """Raised when invitation has already been accepted."""

    def __init__(self):
        """Initialize invitation already accepted error."""
        super().__init__(
            message="Invitation has already been accepted",
            resource="invitation",
        )


class InsufficientPermissionsError(PermissionDeniedError):
    """Raised when user lacks required permissions for organization operations."""

    def __init__(self, action: str):
        """
        Initialize insufficient permissions error.

        Args:
            action: The action that was denied
        """
        super().__init__(action=action, resource="this organization")


class NotOrganizationMemberError(PermissionDeniedError):
    """Raised when user is not a member of the organization."""

    def __init__(self):
        """Initialize not organization member error."""
        super().__init__(action="access", resource="this organization")
        self.message = "You are not a member of this organization"


class LastOwnerRemovalError(BusinessRuleViolationError):
    """Raised when attempting to remove or change role of the last owner."""

    def __init__(self):
        """Initialize last owner removal error."""
        super().__init__(
            message="Cannot remove the last owner from the organization",
            rule="minimum_one_owner",
        )
