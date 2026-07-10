"""HCP API query and response schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.common import AuditSchema, SchemaBase
from app.schemas.hcp import HcpResponse


class HcpSearchQuery(SchemaBase):
    """Query parameters for HCP search."""

    doctor_name: str | None = Field(default=None, description="Doctor or HCP name.")
    hospital: str | None = Field(default=None, description="Hospital or clinic name.")
    city: str | None = Field(default=None, description="City filter.")
    specialization: str | None = Field(default=None, description="Medical specialization.")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class HcpHistoryItem(SchemaBase):
    """Summary of a previous HCP interaction."""

    interaction_id: UUID
    interaction_date: str
    status: str
    summary: str | None = None
    sentiment: str | None = None
    outcome: str | None = None
    follow_up: str | None = None


class HcpSearchResultItem(HcpResponse):
    """HCP search result enriched with interaction count."""

    previous_interaction_count: int = 0


class HcpHistoryResponse(SchemaBase):
    """HCP interaction history response."""

    hcp_id: UUID
    hcp_name: str
    interactions: list[HcpHistoryItem] = Field(default_factory=list)
