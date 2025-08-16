"""User API routes."""

from typing import List
from uuid import UUID

from core.common.exceptions import DomainException
from core.database import get_session
from core.domains.users import (
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from ...routes.auth.dependencies import get_current_user
from ...utils import handle_domain_exception
from .dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserPublic)
async def create_user(
    user: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Create a new user."""
    try:
        return user_service.create_user(
            session, user_in=user, created_by_id=current_user.id
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/", response_model=List[UserPublic])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """List users with pagination."""
    try:
        return user_service.get_users(
            session, skip=skip, limit=limit, active_only=active_only
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Get a user by ID."""
    try:
        user = user_service.get_user(session, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Convert to public schema
        return UserPublic(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            avatar_url=user.avatar_url,
            auth_user_id=user.auth_user_id,
            is_active=user.is_active,
            permissions=user.permissions,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Update a user."""
    try:
        existing_user = user_service.get_user(session, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        updated_user = user_service.update_user(
            session,
            user=existing_user,
            user_in=user_update,
            updated_by_id=current_user.id,
        )

        # Convert to public schema
        return UserPublic(
            id=updated_user.id,
            full_name=updated_user.full_name,
            email=updated_user.email,
            phone=updated_user.phone,
            avatar_url=updated_user.avatar_url,
            auth_user_id=updated_user.auth_user_id,
            is_active=updated_user.is_active,
            permissions=updated_user.permissions,
            is_superuser=updated_user.is_superuser,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            deleted_at=updated_user.deleted_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Soft delete a user."""
    try:
        success = user_service.delete_user(
            session, user_id=user_id, deleted_by_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return {"message": "User deleted successfully"}
    except DomainException as exc:
        return handle_domain_exception(exc)
