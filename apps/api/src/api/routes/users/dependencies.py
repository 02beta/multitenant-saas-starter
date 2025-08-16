"""User routes specific dependencies."""

from uuid import UUID

from core.domains.users import (
    PasswordService,
    User,
    UserRepository,
    UserService,
)
from fastapi import Depends, HTTPException, status

from ...routes.auth.dependencies import get_current_user


def get_user_repository() -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository()


def get_user_service() -> UserService:
    """Get UserService instance."""
    user_repository = UserRepository()
    password_service = PasswordService()
    return UserService(user_repository, password_service)


async def validate_user_access(
    user_id: UUID, current_user: User = Depends(get_current_user)
) -> bool:
    """Validate user has access to user resource."""
    if current_user.is_superuser or current_user.id == user_id:
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
    )
