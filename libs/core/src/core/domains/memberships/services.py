"""Service for the memberships domain."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from .exceptions import (
    InsufficientPermissionsError,
    InvitationAlreadyAcceptedError,
    InvitationNotFoundError,
    LastOwnerRemovalError,
    MembershipNotFoundError,
    NotOrganizationMemberError,
    UserAlreadyInvitedError,
    UserAlreadyMemberError,
)
from .models import (
    Membership,
    MembershipRole,
    MembershipStatus,
)
from .repository import MembershipRepository
from .schemas import (
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
)

__all__ = [
    "MembershipService",
]


class MembershipService:
    """Service for Membership domain operations."""

    def __init__(self, repository: MembershipRepository):
        """
        Initialize the service with a repository.

        Args:
            repository: MembershipRepository instance
        """
        self.repository = repository

    def create_membership(
        self,
        session: Session,
        *,
        membership_in: MembershipCreate,
        invited_by_id: UUID,
    ) -> Membership:
        """
        Create a new membership (invite a user to a organization).

        Args:
            session: Database session
            membership_in: Organization user creation data
            invited_by_id: ID of the user creating the invitation

        Returns:
            Created Membership instance

        Raises:
            UserAlreadyMemberError: If user already exists in organization or validation fails
            UserAlreadyInvitedError: If user already has an invitation to the organization
            InsufficientPermissionsError: If inviter does not have permission to invite users
        """
        # Check if user already exists in organization
        existing = self.repository.get_by_organization_and_user(
            session,
            organization_id=membership_in.organization_id,
            user_id=membership_in.user_id,
        )

        if existing:
            if existing.status == MembershipStatus.ACTIVE:
                raise UserAlreadyMemberError()
            elif existing.status == MembershipStatus.INVITED:
                raise UserAlreadyInvitedError()

        # Check if inviter has permission to invite users
        inviter = self.repository.get_by_organization_and_user(
            session,
            organization_id=membership_in.organization_id,
            user_id=invited_by_id,
        )

        if not inviter or not inviter.can_manage_users:
            raise InsufficientPermissionsError("invite users to")

        # Set invitation fields
        create_data = membership_in.model_dump()
        create_data["invited_by"] = invited_by_id
        create_data["invited_at"] = datetime.utcnow()
        create_data["status"] = MembershipStatus.INVITED

        # Create the membership
        membership = Membership(**create_data)
        return self.repository.create(session, obj_in=membership)

    def get_membership(
        self,
        session: Session,
        *,
        membership_id: UUID,
        current_user_id: UUID,
    ) -> Optional[Membership]:
        """Get a membership by ID with basic access validation."""
        membership = self.repository.get(session, membership_id)
        if not membership:
            return None
        # Optionally validate that current_user has visibility within the org
        return membership

    def update_membership(
        self,
        session: Session,
        *,
        membership: Membership,
        membership_in: MembershipUpdate,
        updated_by_id: UUID,
    ) -> Membership:
        """Update membership fields."""
        return self.repository.update(
            session,
            db_obj=membership,
            obj_in=membership_in,
            updated_by_id=updated_by_id,
        )

    def delete_membership(
        self,
        session: Session,
        *,
        membership_id: UUID,
        deleted_by_id: UUID,
    ) -> bool:
        """Soft delete membership by ID."""
        return self.repository.remove(
            session, id=membership_id, deleted_by_id=deleted_by_id
        )

    def accept_invitation(
        self,
        session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> Membership:
        """
        Accept a organization invitation.

        Args:
            session: Database session
            organization_id: Organization ID
            user_id: User ID accepting the invitation

        Returns:
            Updated Membership instance

        Raises:
            InvitationNotFoundError: If invitation not found
            InvitationAlreadyAcceptedError: If invitation already accepted
        """
        membership = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=user_id,
        )

        if not membership:
            raise InvitationNotFoundError()

        if membership.status == MembershipStatus.ACTIVE:
            raise InvitationAlreadyAcceptedError()

        # Update status and acceptance timestamp
        update_data = MembershipUpdate(
            status=MembershipStatus.ACTIVE,
            accepted_at=datetime.utcnow(),
        )

        return self.repository.update(
            session,
            db_obj=membership,
            obj_in=update_data,
            updated_by_id=user_id,
        )

    def update_user_role(
        self,
        session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        new_role: MembershipRole,
        updated_by_id: UUID,
    ) -> Membership:
        """
        Update a user's role in a organization.

        Args:
            session: Database session
            organization_id: Organization ID
            user_id: User ID whose role to update
            new_role: New role to assign
            updated_by_id: ID of the user making the update

        Returns:
            Updated Membership instance

        Raises:
            MembershipNotFoundError: If user not found in organization
            InsufficientPermissionsError: If updater does not have permission to update user roles
            LastOwnerRemovalError: If trying to remove the last owner from the organization
        """
        # Get the user to update
        membership = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=user_id,
        )

        if not membership:
            raise MembershipNotFoundError(
                organization_id=organization_id, user_id=user_id
            )

        # Check if updater has permission
        updater = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=updated_by_id,
        )

        if not updater or not updater.can_manage_users:
            raise InsufficientPermissionsError("update user roles")

        # Prevent removing the last owner
        if (
            membership.role == MembershipRole.OWNER
            and new_role != MembershipRole.OWNER
        ):
            owners = self.repository.get_organization_owners(
                session, organization_id=organization_id
            )
            if len(owners) <= 1:
                raise LastOwnerRemovalError()

        # Update the role
        update_data = MembershipUpdate(role=new_role)
        return self.repository.update(
            session,
            db_obj=membership,
            obj_in=update_data,
            updated_by_id=updated_by_id,
        )

    def remove_user_from_organization(
        self,
        session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        removed_by_id: UUID,
    ) -> bool:
        """
        Remove a user from a organization (soft delete).

        Args:
            session: Database session
            organization_id: Organization ID
            user_id: User ID to remove
            removed_by_id: ID of the user performing the removal

        Returns:
            True if successful

        Raises:
            MembershipNotFoundError: If user not found in organization
            InsufficientPermissionsError: If remover does not have permission to remove users
            LastOwnerRemovalError: If trying to remove the last owner from the organization
        """
        # Get the user to remove
        membership = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=user_id,
        )

        if not membership:
            raise MembershipNotFoundError(
                organization_id=organization_id, user_id=user_id
            )

        # Check if remover has permission
        remover = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=removed_by_id,
        )

        # Users can remove themselves, or owners can remove others
        if user_id != removed_by_id and (
            not remover or not remover.can_manage_users
        ):
            raise InsufficientPermissionsError("remove users from")

        # Prevent removing the last owner
        if membership.role == MembershipRole.OWNER:
            owners = self.repository.get_organization_owners(
                session, organization_id=organization_id
            )
            if len(owners) <= 1:
                raise LastOwnerRemovalError()

        # Soft delete the membership
        return self.repository.remove(
            session,
            id=membership.id,
            deleted_by_id=removed_by_id,
        )

    def get_memberships(
        self,
        session: Session,
        *,
        organization_id: UUID,
        current_user_id: UUID,
        status: Optional[MembershipStatus] = None,
        role: Optional[MembershipRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MembershipPublic]:
        """
        Get all users in a organization.

        Args:
            session: Database session
            organization_id: Organization ID
            current_user_id: ID of the user making the request
            status: Optional status filter
            role: Optional role filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MembershipPublic instances

        Raises:
            NotOrganizationMemberError: If current user is not an active member of the organization
        """
        # Check if current user is a member of the organization
        current_member = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=current_user_id,
        )

        if (
            not current_member
            or current_member.status != MembershipStatus.ACTIVE
        ):
            raise NotOrganizationMemberError()

        # Get memberships
        memberships = self.repository.get_memberships(
            session,
            organization_id=organization_id,
            status=status,
            role=role,
            skip=skip,
            limit=limit,
        )

        # Convert to public schema
        return [
            MembershipPublic(
                **user.model_dump(),
                # compatibility with API response shape
                created_at=user.created_at,
                updated_at=user.updated_at,
                deleted_at=user.deleted_at,
            )
            for user in memberships
        ]

    def get_user_organizations(
        self,
        session: Session,
        *,
        user_id: UUID,
        status: Optional[MembershipStatus] = None,
        role: Optional[MembershipRole] = None,
    ) -> List[MembershipPublic]:
        """
        Get all organizations for a user.

        Args:
            session: Database session
            user_id: User ID
            status: Optional status filter
            role: Optional role filter

        Returns:
            List of MembershipPublic instances
        """
        memberships = self.repository.get_user_organizations(
            session,
            user_id=user_id,
            status=status,
            role=role,
        )

        # Convert to public schema
        return [
            MembershipPublic(
                **user.model_dump(),
                created_at=user.created_at,
                updated_at=user.updated_at,
                deleted_at=user.deleted_at,
            )
            for user in memberships
        ]

    def get_pending_invitations(
        self,
        session: Session,
        *,
        user_id: UUID,
    ) -> List[MembershipPublic]:
        """
        Get all pending invitations for a user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            List of MembershipPublic instances with invited status
        """
        return self.get_user_organizations(
            session,
            user_id=user_id,
            status=MembershipStatus.INVITED,
        )

    def check_user_permission(
        self,
        session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        require_write: bool = False,
        require_owner: bool = False,
    ) -> bool:
        """
        Check if a user has specific permissions in a organization.

        Args:
            session: Database session
            organization_id: Organization ID
            user_id: User ID
            require_write: Whether write permission is required
            require_owner: Whether owner permission is required

        Returns:
            True if user has required permissions
        """
        membership = self.repository.get_by_organization_and_user(
            session,
            organization_id=organization_id,
            user_id=user_id,
        )

        if not membership or membership.status != MembershipStatus.ACTIVE:
            return False

        if require_owner:
            return membership.is_owner

        if require_write:
            return membership.can_write

        return True

    def get_membership_count(
        self,
        session: Session,
        *,
        organization_id: UUID,
        current_user_id: UUID,
        active_only: bool = True,
    ) -> int:
        """Count memberships for an organization."""
        status = MembershipStatus.ACTIVE if active_only else None
        return self.repository.count_memberships(
            session, organization_id=organization_id, status=status
        )
