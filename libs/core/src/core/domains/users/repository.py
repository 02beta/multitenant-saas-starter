"""Repository for the users domain."""

import re
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, and_, or_, select

from core.common.protocols import CRUDBase

from .models import User
from .schemas import UserCreate, UserUpdate


class UserRepository(CRUDBase[User, UserCreate, UserUpdate]):
    """Repository for User domain operations."""

    def __init__(self):
        """Initialize the repository with the User model."""
        super().__init__(User)

    def get(self, session: Session, id: UUID) -> Optional[User]:
        """
        Fetch a user by primary key.

        Args:
            session: Database session
            id: User ID

        Returns:
            User instance or None if not found
        """
        return super().get(session, id)

    def get_by_email(self, session: Session, *, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            session: Database session
            email: User's email address

        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(
            and_(
                User.email == email,
                User.deleted_at.is_(None),
            )
        )
        return session.exec(stmt).first()

    def get_active_users(
        self,
        session: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Get all active users.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active User instances
        """
        stmt = (
            select(User)
            .where(
                and_(
                    User.is_active,
                    User.deleted_at.is_(None),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(session.exec(stmt).all())

    def get_superusers(self, session: Session) -> List[User]:
        """
        Get all superusers.

        Args:
            session: Database session

        Returns:
            List of User instances with superuser privileges
        """
        stmt = select(User).where(
            and_(
                User.is_superuser,
                User.is_active,
                User.deleted_at.is_(None),
            )
        )
        return list(session.exec(stmt).all())

    def search_users(
        self,
        session: Session,
        *,
        search_term: str,
        limit: int = 10,
    ) -> List[User]:
        """
        Search users by name or email.

        Args:
            session: Database session
            search_term: Search term to match against name or email
            limit: Maximum number of results to return

        Returns:
            List of User instances matching the search term
        """
        search_pattern = f"%{search_term}%"
        stmt = (
            select(User)
            .where(
                and_(
                    User.deleted_at.is_(None),
                    or_(
                        User.full_name.ilike(search_pattern),
                        User.email.ilike(search_pattern),
                    ),
                )
            )
            .limit(limit)
        )
        return list(session.exec(stmt).all())

    def count_users(
        self,
        session: Session,
        *,
        active_only: bool = True,
    ) -> int:
        """
        Count total number of users.

        Args:
            session: Database session
            active_only: Whether to count only active users

        Returns:
            Total number of users
        """
        stmt = select(User).where(User.deleted_at.is_(None))

        if active_only:
            stmt = stmt.where(User.is_active)

        result = session.exec(stmt)
        return len(result.all())

    def check_email_exists(
        self,
        session: Session,
        *,
        email: str,
        exclude_user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if an email address is already in use.

        Args:
            session: Database session
            email: Email address to check
            exclude_user_id: User ID to exclude from the check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        stmt = select(User).where(
            and_(
                User.email == email,
                User.deleted_at.is_(None),
            )
        )

        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = session.exec(stmt).first()
        return result is not None

    def get_users_by_name(
        self,
        session: Session,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> List[User]:
        """
        Get users by first and/or last name.

        Args:
            session: Database session
            first_name: First name to filter by (optional)
            last_name: Last name to filter by (optional)

        Returns:
            List of User instances matching the name criteria
        """
        conditions = [User.deleted_at.is_(None)]

        if first_name:
            conditions.append(User.full_name.ilike(f"%{first_name}%"))

        if last_name:
            conditions.append(User.full_name.ilike(f"%{last_name}%"))

        stmt = select(User).where(and_(*conditions))
        return list(session.exec(stmt).all())

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
    ) -> List[User]:
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
            List of User instances
        """
        stmt = select(User)

        # Handle soft delete filtering
        if not include_deleted and hasattr(User, "deleted_at"):
            stmt = stmt.where(User.deleted_at.is_(None))

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(User, field):
                    stmt = stmt.where(getattr(User, field) == value)

        # Apply sorting
        if sort_by and hasattr(User, sort_by):
            order_field = getattr(User, sort_by)
            stmt = stmt.order_by(
                order_field.desc() if sort_desc else order_field
            )

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        return list(session.exec(stmt).all())

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """
        Validate email format using regex.

            email: Email address to validate

        Returns:
            True if email format is valid, False otherwise
        """
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        return bool(re.match(pattern, email))
