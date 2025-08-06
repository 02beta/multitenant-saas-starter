"""Organization domain service."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from .exceptions import InvalidOrganizationSlugError, OrganizationAlreadyExistsError
from .models import Organization, OrganizationCreate, OrganizationUpdate
from .repository import OrganizationRepository


class OrganizationService:
    """Service layer for Organization domain business logic."""

    def __init__(self, repository: OrganizationRepository):
        self.repository = repository

    async def create_organization(
        self,
        session: Session,
        *,
        organization_data: OrganizationCreate,
        created_by_id: UUID,
    ) -> Organization:
        """Create a new organization with business logic validation."""

        # Validate slug format
        if not Organization.validate_slug(organization_data.slug):
            raise InvalidOrganizationSlugError(organization_data.slug)

        # Check if slug is available
        existing = self.repository.get_by_slug(session, slug=organization_data.slug)
        if existing:
            raise OrganizationAlreadyExistsError(organization_data.slug)

        # Create organization
        organization = self.repository.create(session, obj_in=organization_data)

        # The membership creation is handled by the memberships domain
        # This demonstrates proper domain separation

        return organization

    async def get_organization(
        self, session: Session, *, organization_id: UUID
    ) -> Optional[Organization]:
        """Get organization by ID."""
        return self.repository.get(session, id=organization_id)

    async def get_organization_by_slug(
        self, session: Session, *, slug: str
    ) -> Optional[Organization]:
        """Get organization by slug."""
        return self.repository.get_by_slug(session, slug=slug)

    async def get_user_organizations(
        self, session: Session, *, user_id: UUID
    ) -> List[Organization]:
        """Get all organizations for a user."""
        return self.repository.get_user_organizations(session, user_id=user_id)

    async def update_organization(
        self,
        session: Session,
        *,
        organization: Organization,
        update_data: OrganizationUpdate,
    ) -> Organization:
        """Update organization with validation."""

        # If updating slug, validate it
        if update_data.slug:
            if not Organization.validate_slug(update_data.slug):
                raise InvalidOrganizationSlugError(update_data.slug)

            # Check if new slug is available (excluding current organization)
            existing = self.repository.get_by_slug(session, slug=update_data.slug)
            if existing and existing.id != organization.id:
                raise OrganizationAlreadyExistsError(update_data.slug)

        return self.repository.update(session, db_obj=organization, obj_in=update_data)

    async def delete_organization(
        self, session: Session, *, organization_id: UUID, deleted_by_id: UUID
    ) -> bool:
        """Soft delete organization with cascade logic."""

        # The actual cascade deletion of memberships should be handled
        # by the memberships domain service

        return self.repository.remove(
            session, id=organization_id, deleted_by_id=deleted_by_id
        )
