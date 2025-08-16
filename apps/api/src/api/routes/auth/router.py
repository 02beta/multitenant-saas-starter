"""Authentication routes router."""

import json
from typing import Optional
from uuid import UUID

from core.database import get_session
from core.domains.auth import AuthService
from core.domains.auth.schemas import (
    ForgotPasswordRequest,
    LoginResponseExtended,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
)
from core.domains.memberships import (
    Membership,
    MembershipStatus,
)
from core.domains.organizations import Organization
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Response,
    status,
)
from pydantic import BaseModel
from sqlmodel import Session, select

from .dependencies import (
    get_auth_service,
    get_current_token,
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
    organization: Optional[dict] = None
    membership: Optional[dict] = None


class EnhancedLoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: Optional[int]
    user: dict
    organization: Optional[dict] = None
    membership: Optional[dict] = None


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: Optional[str] = None,
    session_data: Optional[dict] = None,
    access_token_expires: int = 3600,
    refresh_token_expires: int = 60 * 60 * 24 * 30,
) -> None:
    """Set HTTP-only cookies for access and refresh tokens."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=access_token_expires,
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=refresh_token_expires,
            path="/",
        )
    if session_data:
        # Store session data as JSON in cookie
        response.set_cookie(
            key="session_data",
            value=json.dumps(session_data),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=access_token_expires,
            path="/",
        )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    response.delete_cookie(key="session_data", path="/")


@router.post("/login", response_model=EnhancedLoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    db_session: Session = Depends(get_session),
):
    """Enhanced login with full membership context.

    Sets HTTP-only cookies with user, organization, and membership data.
    """
    try:
        # Authenticate user
        auth_result, session_data = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            organization_id=login_data.organization_id,
        )

        # Get user with membership context
        user_context = await auth_service.get_user_with_membership_context(
            user_id=session_data.user_id,
            organization_id=login_data.organization_id,
        )

        # Prepare session data for cookie
        cookie_session_data = {
            "access_token": auth_result.tokens.access_token,
            "refresh_token": auth_result.tokens.refresh_token,
            "expires_in": auth_result.tokens.expires_in,
            "token_type": auth_result.tokens.token_type,
            "full_name": f"{user_context['user']['first_name']} {user_context['user']['last_name']}",
            "user_id": str(user_context["user"]["id"]),
            "auth_user_id": user_context["user"]["auth_user_id"],
            "organization_id": str(login_data.organization_id)
            if login_data.organization_id
            else None,
            "role": user_context["membership"]["role"]
            if user_context["membership"]
            else None,
            "is_owner": user_context["membership"]["is_owner"]
            if user_context["membership"]
            else False,
            "can_write": user_context["membership"]["can_write"]
            if user_context["membership"]
            else False,
            "can_manage_users": user_context["membership"]["can_manage_users"]
            if user_context["membership"]
            else False,
        }

        set_auth_cookies(
            response,
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            session_data=cookie_session_data,
            access_token_expires=auth_result.tokens.expires_in or 3600,
        )

        return EnhancedLoginResponse(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_in=auth_result.tokens.expires_in,
            user=user_context["user"],
            organization=user_context["organization"],
            membership=user_context["membership"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout")
async def logout(
    response: Response,
    access_token: str = Depends(get_current_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout and invalidate session.

    Clears authentication cookies.
    """
    await auth_service.logout(access_token)
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token.

    Uses refresh_token from HTTP-only cookie if not provided in body.
    Sets new tokens in cookies.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    try:
        auth_result = await auth_service.refresh_session(refresh_token)
        set_auth_cookies(
            response,
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            access_token_expires=auth_result.tokens.expires_in or 3600,
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/me")
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Get current authenticated user profile."""
    return {
        "id": str(current_user.id),
        "auth_user_id": str(current_user.auth_user_id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": f"{current_user.first_name} {current_user.last_name}",
        "avatar_url": current_user.avatar_url,
        "phone": current_user.phone,
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
        "message": (
            "If an account with that email exists, you will receive an email "
            "with a link to reset your password."
        )
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
    access_token: str = Depends(get_current_token),
    auth_service: AuthService = Depends(get_auth_service),
    db_session: Session = Depends(get_session),
):
    """Get current user with organization and memberships."""
    # Get session data
    session_data = await auth_service.validate_session(access_token)

    # Get user with full context
    user_context = await auth_service.get_user_with_membership_context(
        user_id=current_user.id,
        organization_id=session_data.organization_id,
    )

    # Get all memberships
    stmt = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.status == MembershipStatus.ACTIVE,
    )
    memberships = db_session.exec(stmt).all()

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
                    "organization_avatar_url": org.avatar_url,
                    "role": membership.role.name.lower(),
                    "role_value": membership.role.value,
                    "is_owner": membership.is_owner,
                    "is_editor": membership.is_editor,
                    "is_viewer": membership.is_viewer,
                    "can_write": membership.can_write,
                    "can_manage_users": membership.can_manage_users,
                }
            )

    return LoginResponseExtended(
        access_token=access_token,
        refresh_token=session_data.refresh_token,
        token_type="bearer",
        expires_in=3600,
        user=user_context["user"],
        organization=user_context["organization"],
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
                    "avatar_url": org.avatar_url,
                    "logo_url": org.logo_url,
                    "role": membership.role.name.lower(),
                    "role_value": membership.role.value,
                    "is_owner": membership.is_owner,
                    "is_editor": membership.is_editor,
                    "is_viewer": membership.is_viewer,
                    "can_write": membership.can_write,
                    "can_manage_users": membership.can_manage_users,
                }
            )

    return {"organizations": organizations}


@router.post("/switch-organization")
async def switch_organization(
    organization_id: UUID,
    response: Response,
    current_user=Depends(get_current_user),
    access_token: str = Depends(get_current_token),
    auth_service: AuthService = Depends(get_auth_service),
    db_session: Session = Depends(get_session),
):
    """Switch to a different organization.

    Updates the session and sets the organization_id in the session cookie.
    """
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

    # Get session and update organization
    session_data = await auth_service.validate_session(access_token)
    session_data.organization_id = organization_id

    # Get updated context
    user_context = await auth_service.get_user_with_membership_context(
        user_id=current_user.id,
        organization_id=organization_id,
    )

    # Update session cookie
    cookie_session_data = {
        "user_id": str(current_user.id),
        "auth_user_id": str(current_user.auth_user_id),
        "organization_id": str(organization_id),
        "role": user_context["membership"]["role"]
        if user_context["membership"]
        else None,
        "is_owner": user_context["membership"]["is_owner"]
        if user_context["membership"]
        else False,
        "can_write": user_context["membership"]["can_write"]
        if user_context["membership"]
        else False,
        "can_manage_users": user_context["membership"]["can_manage_users"]
        if user_context["membership"]
        else False,
    }

    response.set_cookie(
        key="session_data",
        value=json.dumps(cookie_session_data),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
        path="/",
    )

    return {
        "message": "Organization switched successfully",
        "organization_id": str(organization_id),
        "organization": user_context["organization"],
        "membership": user_context["membership"],
    }
