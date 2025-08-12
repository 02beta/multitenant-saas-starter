"""Authentication routes router."""

from typing import Optional
from uuid import UUID

from core.auth import AuthService, AuthSessionModel
from core.auth.models import (
    ForgotPasswordRequest,
    LoginResponseExtended,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
)
from core.database import get_session
from core.domains.memberships import (
    Membership,
    MembershipRole,
    MembershipStatus,
)
from core.domains.organizations import Organization
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from .dependencies import (
    get_auth_service,
    get_current_session,
    get_current_user,
)

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
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials: {e}",
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
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


@router.post("/signup", response_model=SignupResponse)
async def signup(
    signup_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create new user with organization."""
    try:
        (
            auth_user,
            user_id,
            org_id,
        ) = await auth_service.create_user_with_organization(
            email=signup_data.email,
            password=signup_data.password,
            first_name=signup_data.first_name,
            last_name=signup_data.last_name,
            organization_name=signup_data.organization_name,
        )

        return SignupResponse(
            message="Signup successful, please check your email for a verification link.",
            user_id=str(user_id),
            organization_id=str(org_id),
            requires_email_verification=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(e)}",
        )


@router.post("/forgot-password")
async def forgot_password(
    request_data: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Send password reset email."""
    await auth_service.send_password_reset(request_data.email)
    return {
        "message": "If an account with that email exists, you will receive an email with a link to reset your password."
    }


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reset password with token."""
    success = await auth_service.reset_password(
        reset_data.token, reset_data.password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {
        "message": "Password reset successful, please login with your new password."
    }


@router.get("/me/extended", response_model=LoginResponseExtended)
async def get_current_user_extended(
    current_user=Depends(get_current_user),
    session: AuthSessionModel = Depends(get_current_session),
    db_session: Session = Depends(get_session),
):
    """Get current user with organization and memberships."""
    # Get memberships
    stmt = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.status == MembershipStatus.ACTIVE,
    )
    memberships = db_session.exec(stmt).all()

    # Get current organization if set
    current_org = None
    if session.organization_id:
        stmt = select(Organization).where(
            Organization.id == session.organization_id
        )
        org = db_session.exec(stmt).first()
        if org:
            current_org = {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
            }

    # Build membership list
    membership_list = []
    for membership in memberships:
        stmt = select(Organization).where(
            Organization.id == membership.organization_id
        )
        org = db_session.exec(stmt).first()
        if org:
            membership_list.append(
                {
                    "id": str(membership.id),
                    "organization_id": str(org.id),
                    "organization_name": org.name,
                    "organization_slug": org.slug,
                    "role": membership.role.value,
                    "role_name": membership.role.name,
                }
            )

    # Get session tokens
    # auth_user = await auth_service._get_auth_user_by_session(session)

    return LoginResponseExtended(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        token_type=session.token_type,
        expires_in=3600,
        user={
            "id": str(current_user.id),
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "full_name": current_user.full_name,
        },
        organization=current_org,
        memberships=membership_list,
    )


@router.get("/organizations")
async def get_user_organizations(
    current_user=Depends(get_current_user),
    db_session: Session = Depends(get_session),
):
    """Get all organizations for current user."""
    stmt = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.status == MembershipStatus.ACTIVE,
    )
    memberships = db_session.exec(stmt).all()

    organizations = []
    for membership in memberships:
        stmt = select(Organization).where(
            Organization.id == membership.organization_id
        )
        org = db_session.exec(stmt).first()
        if org:
            organizations.append(
                {
                    "id": str(org.id),
                    "name": org.name,
                    "slug": org.slug,
                    "role": membership.role.value,
                    "role_name": membership.role.name,
                    "is_owner": membership.role == MembershipRole.OWNER,
                }
            )

    return {"organizations": organizations}


@router.post("/switch-organization")
async def switch_organization(
    organization_id: UUID,
    current_user=Depends(get_current_user),
    session: AuthSessionModel = Depends(get_current_session),
    db_session: Session = Depends(get_session),
):
    """Switch to a different organization."""
    # Verify membership
    stmt = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == organization_id,
        Membership.status == MembershipStatus.ACTIVE,
    )
    membership = db_session.exec(stmt).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )

    # Update session
    session.organization_id = organization_id
    db_session.commit()

    return {
        "message": "Organization switched successfully",
        "organization_id": str(organization_id),
    }
