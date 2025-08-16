"""User domain schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """Base User Model."""

    full_name: str = Field(
        nullable=False,
        title="Full Name",
        description="The user's full name",
        min_length=1,
        max_length=64,
    )

    email: str = Field(
        unique=True,
        nullable=False,
        title="Email",
        description="The user's email address",
        min_length=5,
        max_length=320,
        regex=r"^[^@]+@[^@]+\.[^@]+$",
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        title="Phone Number",
        description="User's phone number",
    )

    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        title="Avatar URL",
        description="URL to the user's avatar image",
    )

    auth_user_id: UUID = Field(
        nullable=False,
        title="Auth User ID",
        description="Reference to auth.users.id",
    )

    hashed_password: str = Field(
        min_length=8,
        max_length=512,
        title="Hashed Password",
        description="The user's hashed password",
    )

    is_active: bool = Field(
        default=True,
        nullable=False,
        title="Is Active",
        description="Whether the user is active",
    )

    permissions: Dict[str, Any] = Field(
        default_factory=dict,
        title="Permissions",
        description="User permissions as JSON",
    )

    is_superuser: bool = Field(
        default=False,
        nullable=False,
        title="Is Superuser",
        description="Whether the user is a superuser",
    )


class UserCreate(UserBase):
    """Schema for creating users."""

    pass


class UserUpdate(SQLModel):
    """Schema for updating users."""

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    email: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=320,
        regex=r"^[^@]+@[^@]+\.[^@]+$",
    )
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    auth_user_id: Optional[UUID] = Field(default=None)
    hashed_password: Optional[str] = Field(
        default=None, min_length=8, max_length=512
    )
    is_active: Optional[bool] = Field(default=None)
    permissions: Optional[Dict[str, Any]] = Field(default=None)
    is_superuser: Optional[bool] = Field(default=None)


class UserPublic(SQLModel):
    """Public user schema for API responses."""

    id: UUID
    full_name: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_user_id: Optional[UUID] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
