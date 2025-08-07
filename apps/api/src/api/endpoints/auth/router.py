"""Authentication endpoints router."""

from typing import Optional
from uuid import UUID

from core.auth import AuthResult, AuthService, AuthSessionModel
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .dependencies import get_auth_service, get_current_session, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str
    organization_id: Optional[UUID] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: Optional[int]
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """Login with provider-agnostic authentication."""
    try:
        auth_result = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            organization_id=login_data.organization_id,
        )

        return LoginResponse(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_in=auth_result.tokens.expires_in,
            user={
                "id": auth_result.user.provider_user_id,
                "email": auth_result.user.email,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )


@router.post("/logout")
async def logout(
    session: AuthSessionModel = Depends(get_current_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout and invalidate session."""
    await auth_service.logout(session)
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token."""
    try:
        auth_result = await auth_service.refresh_session(refresh_token)
        return LoginResponse(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_in=auth_result.tokens.expires_in,
            user={
                "id": auth_result.user.provider_user_id,
                "email": auth_result.user.email,
            },
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.get("/me")
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Get current authenticated user profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
    }
