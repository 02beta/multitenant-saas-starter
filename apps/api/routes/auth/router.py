"""Authentication routes router."""

import os

from core.auth import AuthService, AuthSessionModel
from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import (
    get_auth_service,
    get_current_session,
    get_current_user,
)
from .models import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


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
            organization_slug=None,
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
    """Sign up a new user, create an organization and membership, and log in."""
    try:
        # Create user in auth provider with metadata
        user_metadata = {
            "first_name": signup_data.first_name,
            "last_name": signup_data.last_name,
            "phone": signup_data.phone,
            "job_title": signup_data.job_title,
            "company_size": signup_data.company_size,
        }

        # Access the configured provider directly via the service
        provider = auth_service.provider  # type: ignore[attr-defined]
        auth_user = await provider.create_user(
            signup_data.email, signup_data.password, user_metadata
        )

        # Authenticate to obtain tokens and create local session/user
        auth_result = await auth_service.authenticate_user(
            email=signup_data.email,
            password=signup_data.password,
        )

        # Create organization and membership (OWNER)
        from core.database import get_session
        from core.domains.memberships import (
            MembershipCreate,
            MembershipRepository,
            MembershipRole,
            MembershipService,
            MembershipStatus,
        )
        from core.domains.organizations import (
            OrganizationCreate,
            OrganizationRepository,
            OrganizationService,
        )
        from sqlmodel import Session, select

        session_dep = get_session  # type: ignore
        session: Session = session_dep()

        # Resolve local user id from the newly created session
        stmt = select(AuthSessionModel).where(
            AuthSessionModel.access_token == auth_result.tokens.access_token
        )
        auth_session = session.exec(stmt).first()
        if not auth_session:
            raise RuntimeError("Local session not found after authentication")
        local_user_id = auth_session.local_user_id

        org_service = OrganizationService(OrganizationRepository())
        organization = await org_service.create_organization(
            session,
            organization_data=OrganizationCreate(
                name=signup_data.organization_name,
                slug=signup_data.slug,
            ),
            created_by_id=local_user_id,
        )

        membership_service = MembershipService(MembershipRepository())
        membership_service.create_membership(
            session,
            membership_in=MembershipCreate(
                organization_id=organization.id,
                user_id=local_user_id,
                role=MembershipRole.OWNER,
                status=MembershipStatus.ACTIVE,
            ),
            invited_by_id=local_user_id,
        )

        return SignupResponse(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_in=auth_result.tokens.expires_in,
            user={
                "id": auth_user.provider_user_id,
                "email": auth_user.email,
                "first_name": signup_data.first_name,
                "last_name": signup_data.last_name,
            },
            organization_slug=organization.slug,
            organization_id=str(organization.id),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {e}",
        )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Trigger password reset email via Supabase."""
    try:
        # Use Supabase provider directly to avoid changing core protocol
        import supabase_auth
        from core.config import settings

        provider = supabase_auth.create_supabase_provider({
            "supabase_api_url": settings.supabase_api_url,
            "supabase_public_key": settings.supabase_public_key,
            "supabase_secret_key": settings.supabase_secret_key,
            "auth_jwt_secret": settings.auth_jwt_secret,
        })

        redirect_to = request.redirect_url
        if not redirect_to:
            # Default redirect back to web app login with a token handler route
            redirect_to = os.getenv(
                "NEXT_PUBLIC_WEB_BASE_URL", "http://localhost:3000/login"
            )

        provider.client.auth.reset_password_for_email(  # type: ignore[attr-defined]
            request.email,
            options={"redirect_to": redirect_to},
        )
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send reset email: {e}",
        )
