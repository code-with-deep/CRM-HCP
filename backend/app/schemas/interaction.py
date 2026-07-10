"""Interaction Pydantic schemas."""

from datetime import date, time
from uuid import UUID

from pydantic import Field

from app.models.enums import InteractionStatus, Sentiment
from app.schemas.common import AuditSchema, SchemaBase


class InteractionBase(SchemaBase):
    """Shared interaction fields."""

    hcp_id: UUID
    user_id: UUID
    interaction_type_id: UUID
    interaction_date: date
    interaction_time: time | None = None
    summary: str | None = None
    sentiment: Sentiment | None = None
    outcome: str | None = None
    follow_up: str | None = None
    additional_notes: str | None = None
    ai_generated_summary: str | None = None
    conversation_id: UUID | None = None
    status: InteractionStatus = InteractionStatus.DRAFT


class InteractionCreate(InteractionBase):
    """Schema for creating an interaction."""

    created_by: UUID | None = None


class InteractionUpdate(SchemaBase):
    """Schema for updating an interaction."""

    hcp_id: UUID | None = None
    user_id: UUID | None = None
    interaction_type_id: UUID | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    summary: str | None = None
    sentiment: Sentiment | None = None
    outcome: str | None = None
    follow_up: str | None = None
    additional_notes: str | None = None
    ai_generated_summary: str | None = None
    conversation_id: UUID | None = None
    status: InteractionStatus | None = None
    updated_by: UUID | None = None


class InteractionRead(InteractionBase, AuditSchema):
    """Internal read schema for interactions."""


class InteractionResponse(InteractionRead):
    """API response schema for interactions."""
