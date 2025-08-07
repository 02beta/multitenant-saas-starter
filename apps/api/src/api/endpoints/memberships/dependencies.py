"""Membership endpoints dependencies."""

from uuid import UUID

from api.endpoints.auth.dependencies import get_current_user
from core.database import get_session
from core.domains.memberships import (
    MembershipRepository,
    MembershipRole,
    MembershipService,
)
from core.domains.users import User
from fastapi import Depends, HTTPException, status
from sqlmodel import Session


def get_membership_service() -> MembershipService:
    """Get MembershipService instance."""
    membership_repository = MembershipRepository()
    return MembershipService(membership_repository)


async def require_owner_role(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> bool:
    """Require user to be owner of organization."""
    if current_user.is_superuser:
        return True

    membership_service = get_membership_service()
    membership = membership_service.get_user_membership(session, current_user.id, organization_id)

    if not membership or membership.role != MembershipRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    return True


async def require_editor_role(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> bool:
    """Require user to be owner or editor of organization."""
    if current_user.is_superuser:
        return True

    membership_service = get_membership_service()
    membership = membership_service.get_user_membership(session, current_user.id, organization_id)

    if not membership or membership.role not in [
        MembershipRole.OWNER,
        MembershipRole.EDITOR,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor role or higher required",
        )
    return True
