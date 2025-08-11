"""Auth routes dependencies."""

# flake8: noqa: F401
from typing import Optional
from uuid import UUID

import supabase_auth  # Auto-registers Supabase provider
from core.auth import AuthProviderRegistry, AuthService, AuthSessionModel
from core.config import settings
from core.database import get_session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

security = HTTPBearer()


async def get_auth_service(
    session: Session = Depends(get_session),
) -> AuthService:
    """Create auth service with configured provider."""
    provider_config = {
        "api_url": settings.supabase_api_url,
        "anon_key": settings.supabase_public_key,
        "service_role_key": settings.supabase_secret_key,
        "jwt_secret": settings.auth_jwt_secret,
    }

    provider = AuthProviderRegistry.create_provider(
        settings.auth_provider, provider_config
    )

    return AuthService(provider, session)


async def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthSessionModel:
    """Get current authentication session."""
    try:
        return await auth_service.validate_session(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )


async def get_current_user(
    session: AuthSessionModel = Depends(get_current_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current authenticated user."""
    return await auth_service.get_current_user(session)


async def get_current_organization(
    session: AuthSessionModel = Depends(get_current_session),
) -> Optional[UUID]:
    """Get current organization context from session."""
    return session.organization_id
