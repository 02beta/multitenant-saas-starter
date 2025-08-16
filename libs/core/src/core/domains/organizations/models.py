"""Organization domain models."""

from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Index, text
from sqlmodel import Field

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin

from .schemas import OrganizationBase


class Organization(
    OrganizationBase, AuditFieldsMixin, SoftDeleteMixin, table=True
):
    """Organization model for the core domain."""

    __tablename__ = "organizations"
    __table_args__ = (
        Index(
            "idx_organizations_slug",
            "slug",
            unique=False,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_organizations_avatar_url",
            "avatar_url",
            postgresql_where=text(
                "avatar_url IS NOT NULL AND deleted_at IS NULL"
            ),
        ),
        Index("idx_organizations_deleted_at", "deleted_at"),
        {"schema": "org", "extend_existing": True},
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        title="Organization ID",
        description="The organization's unique identifier represented as a uuid4",
    )

    # Organization fields (from SQL script)
    name: str = Field(
        max_length=100,
        nullable=False,
        title="Name",
        description="Display name",
    )
    slug: str = Field(
        max_length=50,
        nullable=False,
        unique=True,
        title="Slug",
        description="URL-friendly identifier",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        nullable=True,
        title="Avatar URL",
        description="URL to the organization's avatar image",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        title="Is Active",
        description="Whether the organization is active",
    )
    owner_id: Optional[UUID] = Field(
        default=None,
        nullable=True,
        title="Owner ID",
        description="Link to owner usr.users record",
        foreign_key="usr.users.id",
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
