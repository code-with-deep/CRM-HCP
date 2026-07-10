"""Conversation Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import ConversationSessionStatus, MessageRole
from app.schemas.common import AuditSchema, SchemaBase


class ConversationSessionBase(SchemaBase):
    """Shared conversation session fields."""

    user_id: UUID
    status: ConversationSessionStatus = ConversationSessionStatus.ACTIVE
    started_at: datetime | None = None
    ended_at: datetime | None = None
    session_metadata: dict[str, Any] | None = None


class ConversationSessionCreate(ConversationSessionBase):
    """Schema for creating a conversation session."""

    created_by: UUID | None = None


class ConversationSessionUpdate(SchemaBase):
    """Schema for updating a conversation session."""

    status: ConversationSessionStatus | None = None
    ended_at: datetime | None = None
    session_metadata: dict[str, Any] | None = None
    updated_by: UUID | None = None


class ConversationSessionRead(ConversationSessionBase, AuditSchema):
    """Internal read schema for conversation sessions."""


class ConversationSessionResponse(ConversationSessionRead):
    """API response schema for conversation sessions."""


class ConversationMessageBase(SchemaBase):
    """Shared conversation message fields."""

    session_id: UUID
    role: MessageRole
    content: str = Field(min_length=1)
    timestamp: datetime | None = None
    tool_called: str | None = Field(default=None, max_length=150)
    sequence_number: int = Field(ge=0)


class ConversationMessageCreate(ConversationMessageBase):
    """Schema for creating a conversation message."""

    created_by: UUID | None = None


class ConversationMessageUpdate(SchemaBase):
    """Schema for updating a conversation message."""

    content: str | None = Field(default=None, min_length=1)
    tool_called: str | None = Field(default=None, max_length=150)
    updated_by: UUID | None = None


class ConversationMessageRead(ConversationMessageBase, AuditSchema):
    """Internal read schema for conversation messages."""


class ConversationMessageResponse(ConversationMessageRead):
    """API response schema for conversation messages."""
