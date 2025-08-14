"""User domain models."""

from uuid import UUID, uuid4

from sqlmodel import Field

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
