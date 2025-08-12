"""Provider-agnostic authentication models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin


class AuthProviderType(str, Enum):
    """Supported authentication provider types."""

    SUPABASE = "supabase"
    AUTH0 = "auth0"
    CLERK = "clerk"
    CUSTOM = "custom"


class TokenPair(SQLModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    expires_at: Optional[datetime] = None


class AuthUser(SQLModel):
    """Provider-agnostic user representation."""

    provider_user_id: str
    email: str
    provider_type: AuthProviderType
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuthResult(SQLModel):
    """Authentication result."""

    user: AuthUser
    tokens: TokenPair
    session_metadata: Dict[str, Any] = Field(default_factory=dict)


class SignupRequest(SQLModel):
    """User signup request."""

    first_name: str = Field(min_length=1, max_length=64)
    last_name: str = Field(min_length=1, max_length=64)
    organization_name: Optional[str] = Field(default=None, max_length=100)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class SignupResponse(SQLModel):
    """Signup response."""

    message: str
    user_id: str
    organization_id: str
    requires_email_verification: bool = True


class ForgotPasswordRequest(SQLModel):
    """Password reset request."""

    email: str = Field(min_length=5, max_length=320)


class ResetPasswordRequest(SQLModel):
    """Reset password request."""

    password: str = Field(min_length=8, max_length=128)
    token: str


class LoginResponseExtended(SQLModel):
    """Extended login response with organization data."""

    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: Optional[int]
    user: dict
    organization: Optional[dict] = None
    memberships: list[dict] = Field(default_factory=list)


class AuthUserModel(SQLModel, AuditFieldsMixin, SoftDeleteMixin, table=True):
    """Provider-agnostic auth user linking table."""

    __tablename__ = "auth_users"
    __table_args__ = {"schema": "identity", "extend_existing": True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    local_user_id: UUID = Field(foreign_key="identity.users.id")
    provider_type: AuthProviderType
    provider_user_id: str = Field(max_length=255)
    provider_email: str = Field(max_length=320)
    provider_metadata: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )


class AuthSessionModel(
    SQLModel, AuditFieldsMixin, SoftDeleteMixin, table=True
):
    """Provider-agnostic auth session table."""

    __tablename__ = "auth_sessions"
    __table_args__ = {"schema": "identity", "extend_existing": True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    local_user_id: UUID = Field(foreign_key="identity.users.id")
    auth_user_id: UUID = Field(foreign_key="identity.auth_users.id")
    access_token: str = Field(max_length=2048)
    refresh_token: Optional[str] = Field(default=None, max_length=2048)
    token_type: str = Field(default="bearer", max_length=50)
    expires_at: datetime
    organization_id: Optional[UUID] = Field(
        default=None, foreign_key="org.organizations.id"
    )
    provider_metadata: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    is_active: bool = Field(default=True)
