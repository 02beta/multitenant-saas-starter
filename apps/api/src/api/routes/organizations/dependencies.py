"""Organization routes dependencies."""

from core.domains.organizations import (
    OrganizationRepository,
    OrganizationService,
)


def get_organization_service() -> OrganizationService:
    """Get OrganizationService instance."""
    repository = OrganizationRepository()
    return OrganizationService(repository)
