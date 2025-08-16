"""User domain models."""

from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index, text
from sqlmodel import Column, Field

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin

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
    __table_args__ = (
        Index(
            "idx_users_email",
            "email",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_users_auth_user_id",
            "auth_user_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("idx_users_deleted_at", "deleted_at"),
        {"schema": "usr", "extend_existing": True},
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        title="User ID",
        description="The user's unique identifier represented as a uuid4",
    )

    # Basic user fields (from SQL script)
    full_name: str = Field(
        max_length=64,
        nullable=False,
        title="Full Name",
        description="The user's full name",
    )
    email: str = Field(
        max_length=320,
        nullable=False,
        unique=True,
        title="Email",
        description="The user's email address",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        title="Phone Number",
        description="User's phone number",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        nullable=True,
        title="Avatar URL",
        description="URL to the user's avatar image",
    )

    # Auth integration fields (from SQL script)
    auth_user_id: UUID = Field(
        nullable=False,
        unique=True,
        title="Auth User ID",
        description="ID of the corresponding user in auth.users",
    )

    hashed_password: str = Field(
        max_length=512,
        nullable=False,
        title="Hashed Password",
        description="The user's hashed password",
    )

    # Permission fields (from SQL script)
    is_active: bool = Field(
        default=True,
        nullable=False,
        title="Is Active",
        description="Whether the user is active",
    )
    permissions: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        title="Permissions",
        description="User permissions as JSON",
    )
    is_superuser: bool = Field(
        default=False,
        nullable=False,
        title="Is Superuser",
        description="Whether the user is a superuser",
    )

    # Override audit FKs to be nullable for users table (bootstrap flow)
    created_by: Optional[UUID] = Field(
        default=None,
        nullable=True,
        foreign_key="usr.users.id",
        title="Created by",
        description="User who created this user (nullable for first user)",
    )
    updated_by: Optional[UUID] = Field(
        default=None,
        nullable=True,
        foreign_key="usr.users.id",
        title="Updated by",
        description="User who last updated this user (nullable for first user)",
    )
