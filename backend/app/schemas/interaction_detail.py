"""Detailed interaction API response schemas."""

from datetime import date, time
from uuid import UUID

from pydantic import Field

from app.models.enums import InteractionStatus, Sentiment
from app.schemas.common import AuditSchema, SchemaBase
from app.schemas.hcp import HcpResponse
from app.schemas.interaction_association import (
    InteractionAttendeeResponse,
    InteractionMaterialResponse,
    InteractionProductResponse,
    InteractionSampleResponse,
    InteractionTopicResponse,
)
from app.schemas.interaction_type import InteractionTypeResponse


class InteractionDetailResponse(AuditSchema):
    """Complete interaction with related associations."""

    hcp_id: UUID
    user_id: UUID
    interaction_type_id: UUID
    conversation_id: UUID | None = None
    interaction_date: date
    interaction_time: time | None = None
    summary: str | None = None
    sentiment: Sentiment | None = None
    outcome: str | None = None
    follow_up: str | None = None
    additional_notes: str | None = None
    ai_generated_summary: str | None = None
    status: InteractionStatus
    hcp: HcpResponse | None = None
    interaction_type: InteractionTypeResponse | None = None
    attendees: list[InteractionAttendeeResponse] = Field(default_factory=list)
    topics: list[InteractionTopicResponse] = Field(default_factory=list)
    materials: list[InteractionMaterialResponse] = Field(default_factory=list)
    samples: list[InteractionSampleResponse] = Field(default_factory=list)
    products: list[InteractionProductResponse] = Field(default_factory=list)
