"""User domain models."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin
from core.domains.auth.schemas import AuthProviderType

from .schemas import UserBase

__all__ = [
    "User",
]


class User(
    UserBase,
    SoftDeleteMixin,
    AuditFieldsMixin,
    table=True,
):
    """User model for the core domain."""

    __tablename__ = "users"
    __table_args__ = ({"schema": "identity", "extend_existing": True},)

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        title="User ID",
        description="The user's unique identifier represented as a uuid4",
    )

    # Provider integration fields
    provider_user_id: Optional[str] = Field(
        default=None,
        max_length=255,
        unique=True,
        nullable=True,
        title="Provider User ID",
        description="ID from the authentication provider (e.g., Supabase auth.users.id)",
    )
    provider_type: Optional[AuthProviderType] = Field(
        default=None,
        nullable=True,
        title="Provider Type",
        description="Type of authentication provider",
    )
    provider_email: Optional[str] = Field(
        default=None,
        max_length=320,
        nullable=True,
        title="Provider Email",
        description="Email from the authentication provider",
    )
    provider_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        title="Provider Metadata",
        description="Additional metadata from the authentication provider",
    )

    # Profile fields
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        nullable=True,
        title="Avatar URL",
        description="URL to the user's avatar image",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        title="Phone Number",
        description="User's phone number",
    )
    job_title: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        title="Job Title",
        description="User's job title",
    )
    organization_name: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        title="Organization Name",
        description="Name of user's organization (for display purposes)",
    )
    last_login_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        title="Last Login Date",
        description="Timestamp of user's last login",
    )
    last_login_location: Optional[str] = Field(
        default=None,
        max_length=255,
        nullable=True,
        title="Last Login Location",
        description="Location of user's last login (IP or geographic)",
    )
    timezone: Optional[str] = Field(
        default=None,
        max_length=50,
        nullable=True,
        title="Timezone",
        description="User's preferred timezone",
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        title="Preferences",
        description="User preferences and settings",
    )

    # Authentication fields
    is_active: bool = Field(
        default=True,
        nullable=False,
        title="Is Active",
        description="Whether the user is active",
    )
    is_superuser: bool = Field(
        default=False,
        nullable=False,
        title="Is Superuser",
        description="Whether the user is a superuser",
    )
    password: Optional[str] = Field(
        default=None,
        nullable=True,
        title="Password (Hashed)",
        description="The user's password is hashed and stored in the database (nullable for external auth)",
        min_length=8,
        max_length=128,
    )
