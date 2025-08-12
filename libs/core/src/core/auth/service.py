"""Core authentication service - uses abstractions only."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from .exceptions import (
    OrganizationAccessDeniedError,
    # UserNotFoundError
    SessionNotFoundError,
)
from .models import AuthResult, AuthSessionModel, AuthUser, AuthUserModel
from .protocols import AuthProvider


class AuthService:
    """Core authentication service that coordinates between providers and local data."""

    def __init__(self, provider: AuthProvider, session: Session):
        self.provider = provider
        self.session = session

    async def authenticate_user(
        self, email: str, password: str, organization_id: Optional[UUID] = None
    ) -> AuthResult:
        """Authenticate user and create local session."""
        # Authenticate with provider (abstracted)
        auth_result = await self.provider.authenticate(email, password)

        # Sync user to local database
        local_user = await self._sync_user_to_local_db(auth_result.user)

        # Validate organization access if specified
        if organization_id:
            await self._validate_organization_access(
                local_user.id, organization_id
            )

        # Create local session
        auth_session = await self._create_local_session(
            auth_result, local_user.id, organization_id
        )

        return auth_result

    async def validate_session(self, access_token: str) -> AuthSessionModel:
        """Validate access token and return session."""
        # Check local session first
        stmt = select(AuthSessionModel).where(
            AuthSessionModel.access_token == access_token,
            AuthSessionModel.is_active,
            AuthSessionModel.expires_at > datetime.utcnow(),
        )
        local_session = self.session.exec(stmt).first()

        if not local_session:
            raise SessionNotFoundError()

        # Validate with provider (abstracted)
        try:
            # flake8: noqa: F841
            user_info = await self.provider.validate_token(access_token)
        except Exception:
            # Token invalid, deactivate local session
            local_session.is_active = False
            self.session.commit()
            raise SessionNotFoundError()

        return local_session

    async def refresh_session(self, refresh_token: str) -> AuthResult:
        """Refresh authentication session."""
        # Get new tokens from provider (abstracted)
        token_pair = await self.provider.refresh_token(refresh_token)

        # Update local session
        stmt = select(AuthSessionModel).where(
            AuthSessionModel.refresh_token == refresh_token,
            AuthSessionModel.is_active,
        )
        session = self.session.exec(stmt).first()

        if not session:
            raise SessionNotFoundError()

        session.access_token = token_pair.access_token
        if token_pair.refresh_token:
            session.refresh_token = token_pair.refresh_token
        if token_pair.expires_at:
            session.expires_at = token_pair.expires_at

        self.session.commit()

        # Return updated auth result
        auth_user = await self._get_auth_user_by_session(session)
        return AuthResult(user=auth_user, tokens=token_pair)

    async def logout(self, session: AuthSessionModel) -> bool:
        """Logout user and invalidate session."""
        # Logout from provider (abstracted)
        auth_user = await self._get_auth_user_by_session(session)
        await self.provider.logout(auth_user.provider_user_id, str(session.id))

        # Deactivate local session
        session.is_active = False
        self.session.commit()

        return True

    async def _sync_user_to_local_db(self, auth_user: AuthUser):
        """Sync provider user to local database."""
        # Check if auth_user already exists
        stmt = select(AuthUserModel).where(
            AuthUserModel.provider_type == auth_user.provider_type,
            AuthUserModel.provider_user_id == auth_user.provider_user_id,
        )
        existing_auth_user = self.session.exec(stmt).first()

        if existing_auth_user:
            # Get existing local user
            from core.domains.users import User

            stmt = select(User).where(
                User.id == existing_auth_user.local_user_id
            )
            local_user = self.session.exec(stmt).first()
            return local_user

        # Create new local user
        from core.domains.users import User

        local_user = User(
            email=auth_user.email,
            first_name="",
            last_name="",
            password="",  # Will be managed by auth provider
        )
        self.session.add(local_user)
        self.session.commit()
        self.session.refresh(local_user)

        # Create auth_user record
        auth_user_record = AuthUserModel(
            local_user_id=local_user.id,
            provider_type=auth_user.provider_type,
            provider_user_id=auth_user.provider_user_id,
            provider_email=auth_user.email,
            provider_metadata=auth_user.provider_metadata,
        )
        self.session.add(auth_user_record)
        self.session.commit()

        return local_user

    async def _create_local_session(
        self,
        auth_result: AuthResult,
        local_user_id: UUID,
        organization_id: Optional[UUID],
    ) -> AuthSessionModel:
        """Create local session record."""
        # Get auth_user record
        stmt = select(AuthUserModel).where(
            AuthUserModel.provider_type == auth_result.user.provider_type,
            AuthUserModel.provider_user_id
            == auth_result.user.provider_user_id,
        )
        auth_user_record = self.session.exec(stmt).first()

        session = AuthSessionModel(
            local_user_id=local_user_id,
            auth_user_id=auth_user_record.id,
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_at=auth_result.tokens.expires_at
            or (datetime.utcnow() + timedelta(hours=1)),
            organization_id=organization_id,
            provider_metadata=auth_result.session_metadata,
        )

        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)

        return session

    async def _validate_organization_access(
        self, user_id: UUID, organization_id: UUID
    ) -> None:
        """Validate user has access to organization."""
        # Check if user is superuser
        from core.domains.users import User

        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()

        if user and user.is_superuser:
            return  # Superusers can access any organization

        # Check membership
        from core.domains.memberships import Membership, MembershipStatus

        stmt = select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == MembershipStatus.ACTIVE,
        )
        membership = self.session.exec(stmt).first()

        if not membership:
            raise OrganizationAccessDeniedError(str(organization_id))

    async def _get_auth_user_by_session(
        self, session: AuthSessionModel
    ) -> AuthUser:
        """Get AuthUser from session."""
        stmt = select(AuthUserModel).where(
            AuthUserModel.id == session.auth_user_id
        )
        auth_user_record = self.session.exec(stmt).first()

        return AuthUser(
            provider_user_id=auth_user_record.provider_user_id,
            email=auth_user_record.provider_email,
            provider_type=auth_user_record.provider_type,
            provider_metadata=auth_user_record.provider_metadata,
            created_at=auth_user_record.created_at,
            updated_at=auth_user_record.updated_at,
        )
