"""User domain schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """Base User Model."""

    email: str = Field(
        unique=True,
        nullable=False,
        title="Email",
        description="The user's email address is also used as the username for authentication",
        min_length=5,
        max_length=320,
        regex=r"^[^@]+@[^@]+\.[^@]+$",
    )

    first_name: str = Field(
        nullable=False,
        title="First Name",
        description="The user's first name",
        min_length=1,
        max_length=64,
    )

    last_name: str = Field(
        nullable=False,
        title="Last Name",
        description="The user's last name",
        min_length=1,
        max_length=64,
    )

    @computed_field(return_type=str)
    @property
    def full_name(self) -> str:
        """The user's full name, computed from first_name and last_name."""
        return f"{self.first_name} {self.last_name}"

    class Config:
        arbitrary_types_allowed = True


class UserCreate(UserBase):
    """Schema for creating users."""

    pass


class UserUpdate(SQLModel):
    """Schema for updating users."""

    email: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=320,
        regex=r"^[^@]+@[^@]+\.[^@]+$",
    )
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    first_name: Optional[str] = Field(
        default=None, min_length=1, max_length=64
    )
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    is_active: Optional[bool] = Field(default=None)
    is_superuser: Optional[bool] = Field(default=None)

    # Profile fields
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    phone: Optional[str] = Field(default=None, max_length=20)
    job_title: Optional[str] = Field(default=None, max_length=100)
    organization_name: Optional[str] = Field(default=None, max_length=100)
    timezone: Optional[str] = Field(default=None, max_length=50)
    preferences: Optional[Dict[str, Any]] = Field(default=None)


class UserPublic(UserBase):
    """Public user schema for API responses."""

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserPublicExtended(UserPublic):
    """Extended public user schema with profile and provider fields."""

    # Provider fields
    provider_user_id: Optional[str] = None
    provider_type: Optional[str] = None
    provider_email: Optional[str] = None

    # Profile fields
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    organization_name: Optional[str] = None
    last_login_date: Optional[datetime] = None
    last_login_location: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
