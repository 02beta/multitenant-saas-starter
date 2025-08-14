"""Organization domain models."""

from uuid import UUID, uuid4

from sqlmodel import Field

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin

from .schemas import OrganizationBase


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
