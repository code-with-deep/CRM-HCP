"""API request schemas for interaction persistence."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import InteractionStatus
from app.schemas.common import SchemaBase


class SaveInteractionRequest(SchemaBase):
    """Request to persist an AI interaction draft to PostgreSQL."""

    user_id: UUID = Field(description="CRM user saving the interaction.")
    conversation_id: UUID | None = Field(
        default=None,
        description="Optional linked conversation session identifier.",
    )
    hcp_id: UUID | None = Field(
        default=None,
        description="Optional explicit HCP identifier override.",
    )
    interaction_draft: dict[str, Any] = Field(
        description="Interaction draft fields from the LangGraph agent.",
        examples=[
            {
                "hcp_name": "Dr. Jane Smith",
                "interaction_type": "Meeting",
                "interaction_date": "2026-07-09",
                "topics_discussed": ["CardioMax efficacy"],
                "materials_shared": ["Product brochure"],
                "samples_distributed": ["CardioMax sample pack"],
                "sentiment": "positive",
                "outcomes": "Positive reception",
                "follow_up_actions": "Schedule follow-up in 2 weeks",
            },
        ],
    )
    status: InteractionStatus = Field(
        default=InteractionStatus.COMPLETED,
        description="Final interaction status after save.",
    )
    ai_generated_summary: str | None = Field(
        default=None,
        description="Optional AI-generated summary to store on the record.",
    )
