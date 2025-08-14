"""Repository for the memberships domain."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, and_, select

from core.common.protocols import CRUDBase

from .models import (
    Membership,
    MembershipRole,
    MembershipStatus,
)
from .schemas import (
    MembershipCreate,
    MembershipUpdate,
)

__all__ = [
    "MembershipRepository",
]


class MembershipRepository(
    CRUDBase[Membership, MembershipCreate, MembershipUpdate]
):
    """Repository for Membership domain operations."""

    def __init__(self):
        """Initialize the repository with the Membership model."""
        super().__init__(Membership)

    def get(self, session: Session, id: UUID) -> Optional[Membership]:
        """
        Fetch a membership by primary key.

        Args:
            session: Database session
            id: Organization user ID

        Returns:
            Membership instance or None if not found
        """
        return super().get(session, id)

    def get_by_organization_and_user(
        self, session: Session, *, organization_id: UUID, user_id: UUID
    ) -> Optional[Membership]:
        """
        Get membership by organization and user IDs.

        Args:
            session: Database session
            organization_id: Organization ID
            user_id: User ID

        Returns:
            Membership instance or None if not found
        """
        stmt = select(Membership).where(
            and_(
                Membership.organization_id == organization_id,
                Membership.user_id == user_id,
                Membership.deleted_at.is_(None),
            )
        )
        return session.exec(stmt).first()

    def get_user_organizations(
        self,
        session: Session,
        *,
        user_id: UUID,
        status: Optional[MembershipStatus] = None,
        role: Optional[MembershipRole] = None,
    ) -> List[Membership]:
        """
        Get all organization relationships for a user.

        Args:
            session: Database session
            user_id: User ID
            status: Optional status filter
            role: Optional role filter

        Returns:
            List of Membership instances
        """
        stmt = select(Membership).where(
            and_(
                Membership.user_id == user_id,
                Membership.deleted_at.is_(None),
            )
        )

        if status is not None:
            stmt = stmt.where(Membership.status == status)

        if role is not None:
            stmt = stmt.where(Membership.role == role)

        return list(session.exec(stmt).all())

    def get_memberships(
        self,
        session: Session,
        *,
        organization_id: UUID,
        status: Optional[MembershipStatus] = None,
        role: Optional[MembershipRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Membership]:
        """
        Get all users for a organization with optional filtering.

        Args:
            session: Database session
            organization_id: Organization ID
            status: Optional status filter
            role: Optional role filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Membership instances
        """
        stmt = select(Membership).where(
            and_(
                Membership.organization_id == organization_id,
                Membership.deleted_at.is_(None),
            )
        )

        if status is not None:
            stmt = stmt.where(Membership.status == status)

        if role is not None:
            stmt = stmt.where(Membership.role == role)

        stmt = stmt.offset(skip).limit(limit)
        return list(session.exec(stmt).all())

    def get_organization_owners(
        self, session: Session, *, organization_id: UUID
    ) -> List[Membership]:
        """
        Get all owners for a organization.

        Args:
            session: Database session
            organization_id: Organization ID

        Returns:
            List of Membership instances with owner role
        """
        return self.get_memberships(
            session,
            organization_id=organization_id,
            role=MembershipRole.OWNER,
            status=MembershipStatus.ACTIVE,
        )

    def get_pending_invitations(
        self, session: Session, *, user_id: UUID
    ) -> List[Membership]:
        """
        Get all pending invitations for a user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            List of Membership instances with invited status
        """
        return self.get_user_organizations(
            session,
            user_id=user_id,
            status=MembershipStatus.INVITED,
        )

    def count_memberships(
        self,
        session: Session,
        *,
        organization_id: UUID,
        status: Optional[MembershipStatus] = None,
    ) -> int:
        """
        Count users in a organization.

        Args:
            session: Database session
            organization_id: Organization ID
            status: Optional status filter

        Returns:
            Number of users in the organization
        """
        stmt = select(Membership).where(
            and_(
                Membership.organization_id == organization_id,
                Membership.deleted_at.is_(None),
            )
        )

        if status is not None:
            stmt = stmt.where(Membership.status == status)

        result = session.exec(stmt)
        return len(result.all())

    def user_has_role_in_any_organization(
        self,
        session: Session,
        *,
        user_id: UUID,
        role: MembershipRole,
    ) -> bool:
        """
        Check if a user has a specific role in any organization.

        Args:
            session: Database session
            user_id: User ID
            role: Role to check for

        Returns:
            True if user has the role in any organization
        """
        stmt = (
            select(Membership)
            .where(
                and_(
                    Membership.user_id == user_id,
                    Membership.role == role,
                    Membership.status == MembershipStatus.ACTIVE,
                    Membership.deleted_at.is_(None),
                )
            )
            .limit(1)
        )

        result = session.exec(stmt).first()
        return result is not None

    def get_records(
        self,
        session: Session,
        *,
        filters: Optional[dict] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[Membership]:
        """
        Get multiple records with dynamic filtering, sorting, and pagination.

        Args:
            session: Database session
            filters: Dictionary of field names and values to filter by
            sort_by: Field name to sort by
            sort_desc: Sort in descending order
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of Membership instances
        """
        stmt = select(Membership)

        # Handle soft delete filtering
        if not include_deleted and hasattr(Membership, "deleted_at"):
            stmt = stmt.where(Membership.deleted_at.is_(None))

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(Membership, field):
                    stmt = stmt.where(getattr(Membership, field) == value)

        # Apply sorting
        if sort_by and hasattr(Membership, sort_by):
            order_field = getattr(Membership, sort_by)
            stmt = stmt.order_by(
                order_field.desc() if sort_desc else order_field
            )

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        return list(session.exec(stmt).all())
