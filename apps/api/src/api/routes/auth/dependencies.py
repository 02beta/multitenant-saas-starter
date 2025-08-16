"""Auth routes dependencies (provider-agnostic)."""

# flake8: noqa: F401
from typing import Optional
from uuid import UUID, uuid4

from core.database import get_session
from core.domains.users import User
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

security = HTTPBearer()


async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current access token from request."""
    return credentials.credentials


async def get_current_user(
    access_token: str = Depends(get_current_token),
    session: Session = Depends(get_session),
) -> User:
    """Resolve the current authenticated user from the token.

    Dev-mode behavior: If token is "uid:<uuid>", fetch that user. Otherwise
    return first active user or create a bootstrap superuser if none exist.
    """
    # If token encodes a user id, try to fetch that user
    user: Optional[User] = None
    if access_token.startswith("uid:"):
        try:
            uid = UUID(access_token.split(":", 1)[1])
            stmt = select(User).where(
                User.id == uid, User.deleted_at.is_(None)
            )
            user = session.exec(stmt).first()
        except Exception:
            user = None

    if not user:
        stmt = select(User).where(User.is_active, User.deleted_at.is_(None))
        user = session.exec(stmt).first()

    if not user:
        bootstrap = User(
            full_name="Bootstrap Admin",
            email="bootstrap@example.com",
            phone=None,
            avatar_url=None,
            auth_user_id=uuid4(),
            hashed_password="bootstrap:unused",
            is_active=True,
            permissions={},
            is_superuser=True,
        )
        session.add(bootstrap)
        session.commit()
        session.refresh(bootstrap)
        bootstrap.created_by = bootstrap.id
        bootstrap.updated_by = bootstrap.id
        session.add(bootstrap)
        session.commit()
        user = bootstrap

    return user


async def get_current_organization() -> Optional[UUID]:
    """Placeholder for organization context. Returns None by default."""
    return None
