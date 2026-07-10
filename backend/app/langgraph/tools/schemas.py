"""Tool input and output schemas for LangGraph CRM tools."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.prompts.schemas import (
    EditInteractionOutput,
    FollowUpUpdateSchema,
    HcpSearchOutput,
    LogInteractionOutput,
    MaterialUpdateSchema,
)


class ToolInputBase(BaseModel):
    """Base schema for tool router inputs.

    Extra fields are ignored so the router can pass extraction hints
    (hcp_name, topics, etc.) without failing tool execution.
    """

    model_config = ConfigDict(extra="ignore")

    user_instruction: str | None = Field(
        default=None,
        description="Latest user instruction driving the tool execution.",
    )


class LogInteractionToolInput(ToolInputBase):
    """Input schema for LogInteractionTool."""

    hcp_name: str | None = None
    interaction_type: str | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: list[str] = Field(default_factory=list)
    topics_discussed: list[str] = Field(default_factory=list)
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    outcomes: str | None = None
    follow_up_actions: str | None = None
    additional_notes: str | None = None
    products: list[str] = Field(default_factory=list)


class EditInteractionToolInput(ToolInputBase):
    """Input schema for EditInteractionTool."""

    hcp_name: str | None = None
    interaction_type: str | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: list[str] | None = None
    topics_discussed: list[str] | None = None
    materials_shared: list[str] | None = None
    samples_distributed: list[str] | None = None
    sentiment: str | None = None
    outcomes: str | None = None
    follow_up_actions: str | None = None
    additional_notes: str | None = None


class SearchHcpToolInput(ToolInputBase):
    """Input schema for SearchHCPTool."""

    doctor_name: str | None = None
    hospital: str | None = None
    city: str | None = None
    specialization: str | None = None


class MaterialsAndSamplesToolInput(ToolInputBase):
    """Input schema for MaterialsAndSamplesTool."""

    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)


class OutcomeAndFollowupToolInput(ToolInputBase):
    """Input schema for OutcomeAndFollowupTool."""

    outcomes: str | None = None
    follow_up_actions: str | None = None
    sentiment: str | None = None
    additional_notes: str | None = None


class HcpSearchResultItem(BaseModel):
    """Single HCP search result enriched with CRM context."""

    model_config = ConfigDict(extra="forbid")

    hcp_id: str
    name: str
    specialization: str | None = None
    hospital: str | None = None
    city: str | None = None
    state: str | None = None
    email: str | None = None
    phone: str | None = None
    previous_interactions: list[dict[str, Any]] = Field(default_factory=list)
    recent_follow_ups: list[str] = Field(default_factory=list)


class SearchHcpToolData(BaseModel):
    """Structured database-backed HCP search results."""

    model_config = ConfigDict(extra="forbid")

    search_reasoning: str
    results: list[HcpSearchResultItem] = Field(default_factory=list)
    total_results: int = 0


class ToolLLMResult(BaseModel):
    """Wrapper for validated LLM structured outputs."""

    model_config = ConfigDict(extra="forbid")

    log_interaction: LogInteractionOutput | None = None
    edit_interaction: EditInteractionOutput | None = None
    hcp_search: HcpSearchOutput | None = None
    materials_update: MaterialUpdateSchema | None = None
    followup_update: FollowUpUpdateSchema | None = None


class ToolExecutionResult(BaseModel):
    """Standard tool execution payload returned to the graph."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    tool_name: str
    message: str
    interaction_patch: dict[str, Any] = Field(default_factory=dict)
    hcp_context: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "EditInteractionToolInput",
    "HcpSearchResultItem",
    "LogInteractionToolInput",
    "MaterialsAndSamplesToolInput",
    "OutcomeAndFollowupToolInput",
    "SearchHcpToolData",
    "SearchHcpToolInput",
    "ToolExecutionResult",
    "ToolInputBase",
    "ToolLLMResult",
]
