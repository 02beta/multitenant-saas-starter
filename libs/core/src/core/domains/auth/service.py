"""Core authentication service - uses abstractions only."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select

from .exceptions import (
    OrganizationAccessDeniedError,
    SessionNotFoundError,
    UserNotFoundError,
)
from .protocols import AuthProvider
from .schemas import AuthResult, AuthUser


class SessionData:
    """Simple session data container."""

    def __init__(
        self,
        user_id: UUID,
        provider_user_id: str,
        organization_id: Optional[UUID] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.provider_user_id = provider_user_id
        self.organization_id = organization_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at or (
            datetime.now(timezone.utc) + timedelta(hours=1)
        )


class AuthService:
    """Core authentication service that coordinates between providers and local data."""

    def __init__(self, provider: AuthProvider, session: Session):
        self.provider = provider
        self.session = session
        # In-memory session store (in production, use Redis or JWT)
        self._sessions: Dict[str, SessionData] = {}

    async def authenticate_user(
        self, email: str, password: str, organization_id: Optional[UUID] = None
    ) -> Tuple[AuthResult, SessionData]:
        """Authenticate user and create session."""
        # Authenticate with provider
        auth_result = await self.provider.authenticate(email, password)

        # Sync user to local database
        local_user = await self._sync_user_to_local_db(auth_result.user)

        # Update last login
        local_user.last_login_date = datetime.now(timezone.utc)
        self.session.commit()

        # Validate organization access if specified
        if organization_id:
            await self._validate_organization_access(
                local_user.id, organization_id
            )

        # Create session
        session_data = SessionData(
            user_id=local_user.id,
            provider_user_id=auth_result.user.provider_user_id,
            organization_id=organization_id,
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            expires_at=auth_result.tokens.expires_at,
        )

        # Store session
        self._sessions[auth_result.tokens.access_token] = session_data

        return auth_result, session_data

    async def validate_session(self, access_token: str) -> SessionData:
        """Validate access token and return session."""
        # Check in-memory session
        session_data = self._sessions.get(access_token)

        if not session_data:
            raise SessionNotFoundError()

        # Check expiration
        if session_data.expires_at < datetime.now(timezone.utc):
            del self._sessions[access_token]
            raise SessionNotFoundError("Session expired")

        # Validate with provider
        try:
            await self.provider.validate_token(access_token)
        except Exception:
            # Remove invalid session
            del self._sessions[access_token]
            raise SessionNotFoundError("Token validation failed")

        return session_data

    async def refresh_session(self, refresh_token: str) -> AuthResult:
        """Refresh authentication session."""
        # Get new tokens from provider
        token_pair = await self.provider.refresh_token(refresh_token)

        # Find and update session
        old_session = None
        for token, session in self._sessions.items():
            if session.refresh_token == refresh_token:
                old_session = session
                del self._sessions[token]
                break

        if not old_session:
            raise SessionNotFoundError()

        # Create new session with updated tokens
        new_session = SessionData(
            user_id=old_session.user_id,
            provider_user_id=old_session.provider_user_id,
            organization_id=old_session.organization_id,
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_at=token_pair.expires_at,
        )

        self._sessions[token_pair.access_token] = new_session

        # Get user for response
        from core.domains.users import User

        stmt = select(User).where(User.id == old_session.user_id)
        user = self.session.exec(stmt).first()

        auth_user = AuthUser(
            provider_user_id=user.provider_user_id,
            email=user.email,
            provider_type=user.provider_type,
            provider_metadata=user.provider_metadata,
        )

        return AuthResult(user=auth_user, tokens=token_pair)

    async def logout(self, access_token: str) -> bool:
        """Logout user and invalidate session."""
        session_data = self._sessions.get(access_token)

        if not session_data:
            return False

        # Logout from provider
        await self.provider.logout(session_data.provider_user_id, access_token)

        # Remove session
        del self._sessions[access_token]

        return True

    async def _sync_user_to_local_db(self, auth_user: AuthUser):
        """Sync provider user to local database."""
        from core.domains.users import User

        # Check if user exists by provider_user_id
        stmt = select(User).where(
            User.provider_user_id == auth_user.provider_user_id
        )
        existing_user = self.session.exec(stmt).first()

        if existing_user:
            # Update provider metadata
            existing_user.provider_metadata = auth_user.provider_metadata
            self.session.commit()
            return existing_user

        # Create new user
        meta = auth_user.provider_metadata or {}
        sb = meta.get("supabase_data", {}) if isinstance(meta, dict) else {}
        email_local = (
            auth_user.email.split("@")[0]
            if "@" in auth_user.email
            else auth_user.email
        )
        first_name = sb.get("first_name") or email_local or "User"
        last_name = sb.get("last_name") or "User"

        new_user = User(
            email=auth_user.email,
            first_name=first_name,
            last_name=last_name,
            password=None,  # External auth
            provider_user_id=auth_user.provider_user_id,
            provider_type=auth_user.provider_type,
            provider_email=auth_user.email,
            provider_metadata=auth_user.provider_metadata,
        )

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        return new_user

    async def _validate_organization_access(
        self, user_id: UUID, organization_id: UUID
    ) -> None:
        """Validate user has access to organization."""
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

    async def get_current_user(self, access_token: str):
        """Get current authenticated user."""
        from core.domains.users import User

        session_data = self._sessions.get(access_token)
        if not session_data:
            raise SessionNotFoundError()

        stmt = select(User).where(User.id == session_data.user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(str(session_data.user_id))
        return user

    async def get_current_user_by_provider_id(self, provider_user_id: str):
        """Get user by provider ID."""
        from core.domains.users import User

        stmt = select(User).where(User.provider_user_id == provider_user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(f"Provider ID: {provider_user_id}")
        return user

    async def create_user_with_organization(
        self,
        email: str,
        phone: str,
        password: str,
        first_name: str,
        last_name: str,
        organization_name: Optional[str] = None,
    ) -> Tuple[AuthUser, UUID, UUID]:
        """Create user with organization and owner membership."""
        # Create user in provider
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "organization_name": organization_name,
        }
        auth_user = await self.provider.create_user(email, password, user_data)

        # Create local user with provider fields
        from slugify import slugify
        from core.domains.memberships import (
            Membership,
            MembershipRole,
            MembershipStatus,
        )
        from core.domains.organizations import Organization
        from core.domains.users import User

        local_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=None,  # External auth
            provider_user_id=auth_user.provider_user_id,
            provider_type=auth_user.provider_type,
            provider_email=auth_user.email,
            provider_metadata=auth_user.provider_metadata,
        )
        self.session.add(local_user)
        self.session.commit()
        self.session.refresh(local_user)

        # Create organization with audit fields
        org_name = (
            organization_name or f"{first_name} {last_name}'s Organization"
        )
        org_slug = slugify(org_name.lower())

        # Ensure unique slug
        base_slug = org_slug
        counter = 1
        while self.session.exec(
            select(Organization).where(Organization.slug == org_slug)
        ).first():
            org_slug = f"{base_slug}-{counter}"
            counter += 1

        organization = Organization(
            name=org_name,
            slug=org_slug,
            description=f"Organization for {first_name} {last_name}",
        )
        self.session.add(organization)
        self.session.commit()
        self.session.refresh(organization)

        # Create owner membership with audit fields
        membership = Membership(
            organization_id=organization.id,
            user_id=local_user.id,
            role=MembershipRole.OWNER,
            status=MembershipStatus.ACTIVE,
            accepted_at=datetime.now(timezone.utc),
        )
        self.session.add(membership)
        self.session.commit()

        return auth_user, local_user.id, organization.id

    async def send_password_reset(self, email: str) -> bool:
        """Send password reset email."""
        try:
            from core.domains.users import User

            stmt = select(User).where(User.email == email)
            user = self.session.exec(stmt).first()

            if user:
                await self.provider.send_password_reset(email)
            return True
        except Exception:
            return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password."""
        try:
            return await self.provider.reset_password(token, new_password)
        except Exception:
            return False

    async def get_user_with_membership_context(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> Dict:
        """Get user with full membership context."""
        from core.domains.users import User
        from core.domains.memberships import Membership, MembershipStatus
        from core.domains.organizations import Organization

        # Get user
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()

        if not user:
            raise UserNotFoundError(str(user_id))

        result = {
            "user": {
                "id": str(user.id),
                "provider_user_id": user.provider_user_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}",
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
            },
            "organization": None,
            "membership": None,
        }

        # Get organization and membership if specified
        if organization_id:
            stmt = select(Organization).where(
                Organization.id == organization_id
            )
            org = self.session.exec(stmt).first()

            if org:
                result["organization"] = {
                    "id": str(org.id),
                    "name": org.name,
                    "slug": org.slug,
                    "avatar_url": org.avatar_url,
                    "logo_url": org.logo_url,
                }

                # Get membership
                stmt = select(Membership).where(
                    Membership.user_id == user_id,
                    Membership.organization_id == organization_id,
                    Membership.status == MembershipStatus.ACTIVE,
                )
                membership = self.session.exec(stmt).first()

                if membership:
                    result["membership"] = {
                        "role": membership.role.name.lower(),
                        "role_value": membership.role.value,
                        "is_owner": membership.is_owner,
                        "is_editor": membership.is_editor,
                        "is_viewer": membership.is_viewer,
                        "can_write": membership.can_write,
                        "can_manage_users": membership.can_manage_users,
                        "status": membership.status.name.lower(),
                    }

        return result
