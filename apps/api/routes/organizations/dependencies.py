"""Organization routes dependencies."""

from uuid import UUID

from core.database import get_session
from core.domains.memberships import MembershipRepository, MembershipService
from core.domains.organizations import (
    OrganizationRepository,
    OrganizationService,
)
from core.domains.users import User
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from ...routes.auth.dependencies import get_current_user


def get_organization_service() -> OrganizationService:
    """Get OrganizationService instance."""
    organization_repository = OrganizationRepository()
    return OrganizationService(organization_repository)


async def validate_organization_access(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> bool:
    """Validate user has access to organization."""
    if current_user.is_superuser:
        return True

    # Check membership
    membership_service = MembershipService(MembershipRepository())
    membership = membership_service.get_user_membership(
        session, current_user.id, organization_id
    )

    if not membership or not membership.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to organization",
        )
    return True
