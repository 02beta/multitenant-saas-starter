"""Memberships domain models."""

from datetime import datetime
from enum import IntEnum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from core.common.mixins import AuditFieldsMixin, SoftDeleteMixin

__all__ = [
    "MembershipRole",
    "MembershipStatus",
    "MembershipBase",
    "Membership",
    "MembershipCreate",
    "MembershipUpdate",
    "MembershipPublic",
]


class MembershipRole(IntEnum):
    """Role enum for memberships."""

    OWNER = 0  # can manage memberships for the organization and edit data associated witht the organization
    EDITOR = 1  # can edit data associated with the organization but not manage memberships
    VIEWER = 2  # can read data associated with the organization


class MembershipStatus(IntEnum):
    """Status enum for memberships."""

    INVITED = 0
    ACTIVE = 1


class MembershipBase(SQLModel):
    """Base membership fields."""

    organization_id: UUID = Field(
        foreign_key="org.organizations.id",
        title="Organization ID",
        description="The ID of the organization this user belongs to",
    )
    user_id: UUID = Field(
        foreign_key="identity.users.id",
        title="User ID",
        description="The ID of the user",
    )
    role: MembershipRole = Field(
        default=MembershipRole.VIEWER,
        title="Role",
        description="The user's role within the organization (0=owner, 1=editor, 2=viewer)",
    )
    status: MembershipStatus = Field(
        default=MembershipStatus.INVITED,
        title="Status",
        description="The user's status within the organization (0=invited, 1=active)",
    )
    invited_by: UUID | None = Field(
        default=None,
        foreign_key="identity.users.id",
        title="Invited By",
        description="The ID of the user who invited this user to the organization",
    )
    invited_at: datetime | None = Field(
        default=None,
        title="Invited At",
        description="The date and time when the user was invited",
    )
    accepted_at: datetime | None = Field(
        default=None,
        title="Accepted At",
        description="The date and time when the user accepted the invitation",
    )


class Membership(
    MembershipBase, AuditFieldsMixin, SoftDeleteMixin, table=True
):
    """Membership model for the core domain."""

    __tablename__ = "memberships"
    __table_args__ = (
        # Ensure a user can only have one active role per organization
        {"schema": "org", "extend_existing": True},
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        title="Membership ID",
        description="The membership relationship's unique identifier represented as a uuid4",
    )

    @property
    def is_owner(self) -> bool:
        """Check if the user is an owner."""
        return self.role == MembershipRole.OWNER

    @property
    def is_editor(self) -> bool:
        """Check if the user is an editor."""
        return self.role == MembershipRole.EDITOR

    @property
    def is_viewer(self) -> bool:
        """Check if the user is a viewer."""
        return self.role == MembershipRole.VIEWER

    @property
    def is_invited(self) -> bool:
        """Check if the user is in invited status."""
        return self.status == MembershipStatus.INVITED

    @property
    def is_active(self) -> bool:
        """Check if the user is active."""
        return self.status == MembershipStatus.ACTIVE

    @property
    def can_write(self) -> bool:
        """Check if the user has write permissions."""
        return self.role in [MembershipRole.OWNER, MembershipRole.EDITOR]

    @property
    def can_manage_users(self) -> bool:
        """Check if the user can manage other users."""
        return self.role == MembershipRole.OWNER


class MembershipCreate(MembershipBase):
    """Schema for creating memberships."""

    # Override defaults to require these fields on creation
    organization_id: UUID = Field(
        ...,
        title="Organization ID",
        description="The ID of the organization this user belongs to",
    )
    user_id: UUID = Field(
        ...,
        title="User ID",
        description="The ID of the user",
    )


class MembershipUpdate(SQLModel):
    """Schema for updating memberships."""

    role: MembershipRole | None = Field(
        default=None,
        title="Role",
        description="The user's role within the organization",
    )
    status: MembershipStatus | None = Field(
        default=None,
        title="Status",
        description="The user's status within the organization",
    )
    accepted_at: datetime | None = Field(
        default=None,
        title="Accepted At",
        description="The date and time when the user accepted the invitation",
    )


class MembershipPublic(MembershipBase):
    """Public membership schema for API responses."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: MembershipRole
    status: MembershipStatus
    invited_by: UUID | None
    invited_at: datetime | None
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime | None = None

    # Additional computed fields for API responses
    is_owner: bool
    is_active: bool
    can_write: bool
    can_manage_users: bool
