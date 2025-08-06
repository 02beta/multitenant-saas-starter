from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import computed_field
from sqlmodel import Field, SQLModel

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin

__all__ = [
    "UserBase",
    "User",
    "UserCreate",
    "UserUpdate",
    "UserPublic",
]


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
    password: str = Field(
        nullable=False,
        title="Password (Hashed)",
        description="The user's password is hashed and stored in the database",
        min_length=8,
        max_length=128,
    )


class UserCreate(UserBase):
    """Schema for creating users."""

    pass


class UserUpdate(SQLModel):
    """Schema for updating users."""

    email: Optional[str] = Field(
        default=None, min_length=5, max_length=320, regex=r"^[^@]+@[^@]+\.[^@]+$"
    )
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    is_active: Optional[bool] = Field(default=None)
    is_superuser: Optional[bool] = Field(default=None)


class UserPublic(UserBase):
    """Public user schema for API responses."""

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
