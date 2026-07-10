"""Topic Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.common import AuditSchema, SchemaBase


class TopicBase(SchemaBase):
    """Shared topic fields."""

    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None


class TopicCreate(TopicBase):
    """Schema for creating a topic."""

    created_by: UUID | None = None


class TopicUpdate(SchemaBase):
    """Schema for updating a topic."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    updated_by: UUID | None = None


class TopicRead(TopicBase, AuditSchema):
    """Internal read schema for topics."""


class TopicResponse(TopicRead):
    """API response schema for topics."""
