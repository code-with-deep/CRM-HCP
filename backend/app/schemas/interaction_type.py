"""Interaction type Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.common import AuditSchema, SchemaBase


class InteractionTypeBase(SchemaBase):
    """Shared interaction type fields."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True


class InteractionTypeCreate(InteractionTypeBase):
    """Schema for creating an interaction type."""

    created_by: UUID | None = None


class InteractionTypeUpdate(SchemaBase):
    """Schema for updating an interaction type."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None
    updated_by: UUID | None = None


class InteractionTypeRead(InteractionTypeBase, AuditSchema):
    """Internal read schema for interaction types."""


class InteractionTypeResponse(InteractionTypeRead):
    """API response schema for interaction types."""
