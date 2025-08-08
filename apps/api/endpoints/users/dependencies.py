"""User endpoints specific dependencies."""

from uuid import UUID

from api.endpoints.auth.dependencies import get_current_user
from core.database import get_session
from core.domains.users import PasswordService, User, UserRepository, UserService
from fastapi import Depends, HTTPException, status
from sqlmodel import Session


def get_user_repository() -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository()


def get_password_service() -> PasswordService:
    """Get PasswordService instance."""
    return PasswordService()


def get_user_session() -> Session:
    """Get Session instance."""
    return get_session()


def get_user_service() -> UserService:
    """Get UserService instance."""
    user_repository = UserRepository()
    password_service = PasswordService()
    return UserService(user_repository, password_service)


async def validate_user_access(user_id: UUID, current_user: User = Depends(get_current_user)) -> bool:
    """Validate user has access to user resource."""
    if current_user.is_superuser or current_user.id == user_id:
        return True
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
