"""Organization domain repository."""

from typing import List, Optional
from uuid import uuid4

from sqlmodel import Session, and_, select

from core.common.protocols import CRUDBase

from .models import Organization, OrganizationCreate, OrganizationUpdate


class OrganizationRepository(
    CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]
):
    """Repository for Organization domain operations."""

    def __init__(self):
        super().__init__(Organization)

    def get_by_slug(self, session: Session, *, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        stmt = select(Organization).where(
            and_(Organization.slug == slug, Organization.deleted_at.is_(None))
        )
        return session.exec(stmt).first()

    def get_user_organizations(
        self, session: Session, *, user_id: uuid4
    ) -> List[Organization]:
        """Get all organizations for a user."""
        from ..memberships.models import Membership

        stmt = (
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(
                and_(
                    Membership.user_id == user_id,
                    Organization.deleted_at.is_(None),
                    Membership.deleted_at.is_(None),
                )
            )
        )
        return list(session.exec(stmt).all())

    def search_by_name(
        self, session: Session, *, search_term: str, limit: int = 10
    ) -> List[Organization]:
        """Search organizations by name."""
        stmt = (
            select(Organization)
            .where(
                and_(
                    Organization.deleted_at.is_(None),
                    Organization.name.ilike(f"%{search_term}%"),
                )
            )
            .limit(limit)
        )
        return list(session.exec(stmt).all())

    def get_active_organizations_by_plan(
        self, session: Session, *, plan_name: str
    ) -> List[Organization]:
        """Get all active organizations on a specific plan."""
        stmt = select(Organization).where(
            and_(
                Organization.plan_name == plan_name,
                Organization.is_active,
                Organization.deleted_at.is_(None),
            )
        )
        return list(session.exec(stmt).all())
