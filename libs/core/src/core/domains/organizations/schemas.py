"""Organization domain schemas."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


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
