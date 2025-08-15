"""Shared mixins for all domains."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field


def utcnow() -> datetime:
    """Return the current UTC datetime with timezone info."""

    return datetime.now(timezone.utc)


class AuditFieldsMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        title="Created at",
        description="The date and time the record was created",
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        title="Updated at",
        description="The date and time the record was last updated",
    )
    created_by: UUID = Field(
        default_factory=uuid4,
        nullable=False,
        title="Created by",
        description="The user who created the record",
        foreign_key="identity.users.id",
    )
    updated_by: UUID = Field(
        default_factory=uuid4,
        nullable=False,
        title="Updated by",
        description="The user who updated the record",
        foreign_key="identity.users.id",
    )

    def set_audit_fields(self, updated_by_id: Optional[UUID] = None) -> None:
        """Update audit fields."""
        self.updated_at = utcnow()
        if updated_by_id is not None:
            self.updated_by = updated_by_id


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        title="Deleted at",
        description="The date and time the record was deleted",
    )
    deleted_by: Optional[UUID] = Field(
        default=None,
        nullable=True,
        title="Deleted by",
        description="The user who deleted the record",
        foreign_key="identity.users.id",
    )

    def soft_delete(self, deleted_by_id: Optional[UUID] = None) -> None:
        """Mark record as soft deleted."""
        self.deleted_at = utcnow()
        self.deleted_by = deleted_by_id

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None
