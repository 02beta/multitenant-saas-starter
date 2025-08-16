"""Organization Users API routes."""

from typing import List
from uuid import UUID

from core.common.exceptions import DomainException
from core.database import get_session
from core.domains.memberships import (
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
)
from core.domains.users import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ...routes.auth.dependencies import get_current_user
from ...utils import handle_domain_exception
from .dependencies import get_membership_service

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.post("/", response_model=MembershipPublic)
async def create_membership(
    membership: MembershipCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
):
    """Create a new membership in org.memberships."""
    try:
        return membership_service.create_membership(
            session, membership_in=membership, invited_by_id=current_user.id
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/", response_model=List[MembershipPublic])
async def list_memberships(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
):
    """List memberships from org.memberships."""
    try:
        return membership_service.get_memberships(
            session,
            organization_id=organization_id,
            current_user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/{membership_id}", response_model=MembershipPublic)
async def get_membership(
    membership_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
):
    """Get a membership by ID from org.memberships."""
    try:
        membership = membership_service.get_membership(
            session,
            membership_id=membership_id,
            current_user_id=current_user.id,
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization user not found",
            )
        return membership
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.put("/{membership_id}", response_model=MembershipPublic)
async def update_membership(
    membership_id: UUID,
    membership_update: MembershipUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
):
    """Update a membership in org.memberships."""
    try:
        existing_membership = membership_service.get_membership(
            session,
            membership_id=membership_id,
            current_user_id=current_user.id,
        )
        if not existing_membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization user not found",
            )
        return membership_service.update_membership(
            session,
            membership=existing_membership,
            membership_in=membership_update,
            updated_by_id=current_user.id,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.delete("/{membership_id}")
async def delete_membership(
    membership_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
):
    """Soft delete a membership in org.memberships."""
    try:
        success = membership_service.delete_membership(
            session,
            membership_id=membership_id,
            deleted_by_id=current_user.id,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization user not found",
            )
        return {"message": "Organization user deleted successfully"}
    except DomainException as exc:
        return handle_domain_exception(exc)
