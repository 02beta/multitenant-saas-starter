"""User API routes."""

from typing import List
from uuid import UUID

from api.endpoints.auth.dependencies import get_current_user
from api.utils import handle_domain_exception
from core.common.exceptions import DomainException
from core.database import get_session
from core.domains.users import (
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session

from .dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["users"])


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""

    current_password: str
    new_password: str


class GeneratePasswordResponse(BaseModel):
    """Schema for generated password response."""

    password: str


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
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
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
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            is_active=updated_user.is_active,
            is_superuser=updated_user.is_superuser,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
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


@router.post("/{user_id}/activate", response_model=UserPublic)
async def activate_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Activate a user account."""
    try:
        existing_user = user_service.get_user(session, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        activated_user = user_service.activate_user(
            session, user=existing_user, activated_by_id=current_user.id
        )

        # Convert to public schema
        return UserPublic(
            id=activated_user.id,
            email=activated_user.email,
            first_name=activated_user.first_name,
            last_name=activated_user.last_name,
            is_active=activated_user.is_active,
            is_superuser=activated_user.is_superuser,
            created_at=activated_user.created_at,
            updated_at=activated_user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.post("/{user_id}/deactivate", response_model=UserPublic)
async def deactivate_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Deactivate a user account."""
    try:
        existing_user = user_service.get_user(session, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        deactivated_user = user_service.deactivate_user(
            session, user=existing_user, deactivated_by_id=current_user.id
        )

        # Convert to public schema
        return UserPublic(
            id=deactivated_user.id,
            email=deactivated_user.email,
            first_name=deactivated_user.first_name,
            last_name=deactivated_user.last_name,
            is_active=deactivated_user.is_active,
            is_superuser=deactivated_user.is_superuser,
            created_at=deactivated_user.created_at,
            updated_at=deactivated_user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.post("/{user_id}/promote", response_model=UserPublic)
async def promote_to_superuser(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Promote user to superuser status."""
    try:
        existing_user = user_service.get_user(session, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        promoted_user = user_service.promote_to_superuser(
            session, user=existing_user, promoted_by_id=current_user.id
        )

        # Convert to public schema
        return UserPublic(
            id=promoted_user.id,
            email=promoted_user.email,
            first_name=promoted_user.first_name,
            last_name=promoted_user.last_name,
            is_active=promoted_user.is_active,
            is_superuser=promoted_user.is_superuser,
            created_at=promoted_user.created_at,
            updated_at=promoted_user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.post("/{user_id}/revoke-superuser", response_model=UserPublic)
async def revoke_superuser(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Revoke superuser status from user."""
    try:
        existing_user = user_service.get_user(session, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        revoked_user = user_service.revoke_superuser(
            session, user=existing_user, revoked_by_id=current_user.id
        )

        # Convert to public schema
        return UserPublic(
            id=revoked_user.id,
            email=revoked_user.email,
            first_name=revoked_user.first_name,
            last_name=revoked_user.last_name,
            is_active=revoked_user.is_active,
            is_superuser=revoked_user.is_superuser,
            created_at=revoked_user.created_at,
            updated_at=revoked_user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.post("/{user_id}/change-password", response_model=UserPublic)
async def change_password(
    user_id: UUID,
    password_change: PasswordChangeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Change user's password."""
    try:
        existing_user = user_service.get_user(session, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        updated_user = user_service.change_password(
            session,
            user=existing_user,
            current_password=password_change.current_password,
            new_password=password_change.new_password,
            updated_by_id=current_user.id,
        )

        # Convert to public schema
        return UserPublic(
            id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            is_active=updated_user.is_active,
            is_superuser=updated_user.is_superuser,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/search/by-name", response_model=List[UserPublic])
async def search_users_by_name(
    search_term: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Search users by name or email."""
    try:
        return user_service.search_users(session, search_term=search_term, limit=limit)
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/email/{email}", response_model=UserPublic)
async def get_user_by_email(
    email: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Get a user by email address."""
    try:
        user = user_service.get_user_by_email(session, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Convert to public schema
        return UserPublic(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/count")
async def get_user_count(
    active_only: bool = Query(True),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    """Get total count of users."""
    try:
        count = user_service.get_user_count(session, active_only=active_only)
        return {"count": count}
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.post("/generate-password", response_model=GeneratePasswordResponse)
async def generate_secure_password(
    length: int = Query(16, ge=12, le=128),
    current_user: User = Depends(get_current_user),
):
    """Generate a secure random password."""
    try:
        from core.domains.users import PasswordService

        password = PasswordService.generate_secure_password(length=length)
        return GeneratePasswordResponse(password=password)
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.post("/authenticate")
async def authenticate_user(
    email: str,
    password: str,
    session: Session = Depends(get_session),
    user_service=Depends(get_user_service),
):
    """Authenticate a user by email and password."""
    try:
        user = user_service.authenticate_user(session, email=email, password=password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Convert to public schema
        return UserPublic(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    except DomainException as exc:
        return handle_domain_exception(exc)
