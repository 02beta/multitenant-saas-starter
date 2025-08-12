"""Organization domain models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin


class OrganizationBase(SQLModel):
    """Base organization fields."""

    name: str = Field(min_length=1, max_length=100, description="Display name")
    slug: str = Field(
        min_length=3,
        max_length=50,
        regex=r"^[a-z0-9-]+$",
        description="URL-friendly identifier",
    )
    description: str | None = Field(default=None, max_length=500)
    website: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=512)


class Organization(
    OrganizationBase, AuditFieldsMixin, SoftDeleteMixin, table=True
):
    """Organization model for the core domain."""

    __tablename__ = "organizations"
    __table_args__ = ({"schema": "org", "extend_existing": True},)

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        title="Organization ID",
        description="The organization's unique identifier represented as a uuid4",
    )

    is_active: bool = Field(
        default=True,
        nullable=False,
        title="Is Active",
        description="Whether the organization is active",
    )

    @staticmethod
    def validate_slug(slug: str) -> bool:
        """
        Validate organization slug format.

        Args:
            slug: Slug to validate

        Returns:
            True if valid, False otherwise
        """
        import re

        return bool(re.match(r"^[a-z0-9-]+$", slug))


class OrganizationCreate(OrganizationBase):
    """Schema for creating organizations."""

    pass


class OrganizationUpdate(SQLModel):
    """Schema for updating organizations."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    website: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None


class OrganizationPublic(OrganizationBase):
    """Public organization schema for API responses."""

    id: UUID
    is_active: bool
    plan_name: str | None = None
    max_members: int
    member_count: int
    created_at: datetime
    updated_at: datetime | None = None
