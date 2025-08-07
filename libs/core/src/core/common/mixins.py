"""Shared mixins for all domains."""

from datetime import datetime
from typing import Optional
from uuid import UUID

# from zoneinfo import ZoneInfo
from sqlmodel import Field

# def datetime_to_gmt_str(dt: datetime) -> str:
#     """Convert datetime to GMT string format."""
#     if not dt.tzinfo:
#         dt = dt.replace(tzinfo=ZoneInfo("UTC"))

#     return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


# class BaseModel(SQLModel):
#     """Base model with custom datetime serialization."""

#     def model_dump(self, **kwargs) -> dict:
#         """Override model_dump to serialize datetime fields as GMT strings."""
#         data = super().model_dump(**kwargs)

#         # Convert datetime fields to GMT strings
#         for key, value in data.items():
#             if isinstance(value, datetime):
#                 data[key] = datetime_to_gmt_str(value)

#         return data


class AuditFieldsMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        title="Created at",
        description="The date and time the record was created",
    )
    updated_at: Optional[datetime] = Field(
        default=datetime.utcnow,
        nullable=False,
        title="Updated at",
        description="The date and time the record was last updated",
    )
    created_by: Optional[UUID] = Field(
        default=None,
        nullable=False,
        title="Created by",
        description="The user who created the record",
        foreign_key="identity.users.id",
    )
    updated_by: Optional[UUID] = Field(
        default=None,
        nullable=False,
        title="Updated by",
        description="The user who updated the record",
        foreign_key="identity.users.id",
    )

    def set_audit_fields(self, updated_by_id: Optional[UUID] = None) -> None:
        """Update audit fields."""
        self.updated_at = datetime.utcnow()
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
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_id

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None
