"""Memberships domain schemas."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from .models import MembershipRole, MembershipStatus

__all__ = [
    "MembershipBase",
    "MembershipCreate",
    "MembershipUpdate",
    "MembershipPublic",
]


class MembershipBase(SQLModel):
    """Base membership fields."""

    organization_id: UUID = Field(
        foreign_key="org.organizations.id",
        title="Organization ID",
        description="The ID of the organization this user belongs to",
    )
    user_id: UUID = Field(
        foreign_key="usr.users.id",
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
        foreign_key="usr.users.id",
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


class MembershipCreate(MembershipBase):
    """Schema for creating memberships."""

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
    deleted_at: datetime | None = None
