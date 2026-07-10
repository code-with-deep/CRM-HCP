"""Structured output schemas for LangGraph node decisions."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentIntent(str, Enum):
    """High-level intents recognized by the intent reasoner."""

    LOG_INTERACTION = "log_interaction"
    EDIT_INTERACTION = "edit_interaction"
    SEARCH_HCP = "search_hcp"
    UPDATE_MATERIALS = "update_materials"
    UPDATE_SAMPLES = "update_samples"
    UPDATE_OUTCOMES = "update_outcomes"
    UPDATE_FOLLOW_UP = "update_follow_up"
    GENERAL_ASSISTANCE = "general_assistance"
    UNKNOWN = "unknown"


class ToolName(str, Enum):
    """Registered LangGraph tool identifiers."""

    LOG_INTERACTION = "log_interaction"
    EDIT_INTERACTION = "edit_interaction"
    SEARCH_HCP = "search_hcp"
    MATERIALS_AND_SAMPLES = "materials_and_samples"
    OUTCOME_AND_FOLLOWUP = "outcome_and_followup"
    NONE = "none"


class ToolExtractionHints(BaseModel):
    """Fields the planner may pre-extract for tool execution."""

    model_config = ConfigDict(extra="ignore")

    user_instruction: str | None = None
    hcp_name: str | None = None
    doctor_name: str | None = None
    interaction_type: str | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: list[str] = Field(default_factory=list)
    topics_discussed: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    outcomes: str | None = None
    follow_up_actions: str | None = None
    additional_notes: str | None = None
    hospital: str | None = None
    city: str | None = None
    specialization: str | None = None


class PlannerOutput(BaseModel):
    """Structured orchestration output from the planner node.

    Intent and tool routing are decided in this single LLM call so downstream
    graph nodes can stay fast under API rate limits.
    """

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(description="What the agent should accomplish for this turn.")
    requires_tool_execution: bool = Field(
        description="Whether a tool must be executed to satisfy the request.",
    )
    context_summary: str = Field(
        description="Summary of relevant conversation and interaction context.",
    )
    constraints: list[str] = Field(default_factory=list)

    # Intent (consumed by intent_reasoner_node without a second LLM call)
    primary_intent: AgentIntent = Field(
        default=AgentIntent.UNKNOWN,
        description="Primary semantic intent for this turn.",
    )
    secondary_intents: list[AgentIntent] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = Field(
        default="",
        description="Brief reasoning for the intent and tool choice.",
    )
    requires_clarification: bool = False
    clarification_question: str | None = None

    # Routing (consumed by tool_router_node without a second LLM call)
    selected_tool: ToolName = Field(
        default=ToolName.NONE,
        description="Tool to execute, or none when only a conversational reply is needed.",
    )
    tool_input: ToolExtractionHints = Field(
        default_factory=ToolExtractionHints,
        description="Pre-extracted CRM fields and user_instruction for the selected tool.",
    )
    routing_reasoning: str = Field(
        default="",
        description="Why this tool was selected.",
    )
    should_execute_tool: bool = Field(
        default=False,
        description="True when selected_tool should run this turn.",
    )


class IntentReasonerOutput(BaseModel):
    """Structured output from the intent reasoner node."""

    model_config = ConfigDict(extra="forbid")

    primary_intent: AgentIntent
    secondary_intents: list[AgentIntent] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    requires_clarification: bool = False
    clarification_question: str | None = None


class ToolRouterOutput(BaseModel):
    """Structured output from the LLM-driven tool router."""

    model_config = ConfigDict(extra="forbid")

    selected_tool: ToolName
    tool_input: dict[str, Any] = Field(default_factory=dict)
    routing_reasoning: str
    should_execute_tool: bool = True


class ValidationOutput(BaseModel):
    """Structured validation result for tool execution output."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    normalized_result: dict[str, Any] = Field(default_factory=dict)
    should_retry: bool = False


class ResponseGeneratorOutput(BaseModel):
    """Structured output for the final assistant response."""

    model_config = ConfigDict(extra="forbid")

    message: str
    suggested_prompts: list[str] = Field(default_factory=list)
