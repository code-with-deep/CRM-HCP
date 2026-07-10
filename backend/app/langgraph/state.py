"""Strongly typed LangGraph agent state definitions."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field

from app.langgraph.schemas import (
    IntentReasonerOutput,
    PlannerOutput,
    ResponseGeneratorOutput,
    ToolName,
    ToolRouterOutput,
    ValidationOutput,
)


class InteractionDraft(BaseModel):
    """Serializable interaction draft synchronized with the CRM form."""

    model_config = ConfigDict(extra="forbid")

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

    def to_serializable(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_serializable(cls, value: dict[str, Any] | None) -> InteractionDraft:
        """Hydrate an interaction draft from serialized state."""
        if not value:
            return cls()
        return cls.model_validate(value)


class HcpContext(BaseModel):
    """Current HCP focus for the active conversation."""

    model_config = ConfigDict(extra="forbid")

    hcp_id: str | None = None
    name: str | None = None
    specialization: str | None = None
    hospital: str | None = None
    city: str | None = None
    state: str | None = None

    def to_serializable(self) -> dict[str, Any] | None:
        """Return a JSON-serializable dictionary when populated."""
        if not any(self.model_dump().values()):
            return None
        return self.model_dump(mode="json")

    @classmethod
    def from_serializable(cls, value: dict[str, Any] | None) -> HcpContext | None:
        """Hydrate HCP context from serialized state."""
        if not value:
            return None
        return cls.model_validate(value)


class UserContext(BaseModel):
    """Authenticated user metadata passed into the graph."""

    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    role: str | None = None
    display_name: str | None = None
    timezone: str = "UTC"

    def to_serializable(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_serializable(cls, value: dict[str, Any] | None) -> UserContext:
        """Hydrate user context from serialized state."""
        if not value:
            return cls()
        return cls.model_validate(value)


class ConversationMemory(BaseModel):
    """Conversation memory persisted inside graph state."""

    model_config = ConfigDict(extra="forbid")

    turn_count: int = 0
    last_user_message: str | None = None
    last_assistant_message: str | None = None
    last_tool_name: str | None = None
    interaction_history_summary: str | None = None
    remembered_fields: list[str] = Field(default_factory=list)

    def to_serializable(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_serializable(cls, value: dict[str, Any] | None) -> ConversationMemory:
        """Hydrate memory from serialized state."""
        if not value:
            return cls()
        return cls.model_validate(value)


class AgentState(TypedDict, total=False):
    """Primary LangGraph state for the Healthcare CRM AI agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    conversation_id: str | None
    current_interaction: dict[str, Any]
    current_hcp: dict[str, Any] | None
    selected_tool: str | None
    tool_result: dict[str, Any] | None
    interaction_status: str
    user_context: dict[str, Any]
    memory: dict[str, Any]
    validation_errors: list[str]
    response: str | None

    planner_output: dict[str, Any] | None
    intent_output: dict[str, Any] | None
    router_output: dict[str, Any] | None
    validation_output: dict[str, Any] | None
    response_output: dict[str, Any] | None
    retry_count: int
    error_message: str | None


def create_initial_state(
    *,
    user_message: str,
    conversation_id: str | None = None,
    current_interaction: InteractionDraft | None = None,
    current_hcp: HcpContext | None = None,
    user_context: UserContext | None = None,
    memory: ConversationMemory | None = None,
) -> AgentState:
    """Create an initial graph state for a new user turn."""
    from langchain_core.messages import HumanMessage

    draft = current_interaction or InteractionDraft()
    context = user_context or UserContext()
    conversation_memory = memory or ConversationMemory()
    # Always stamp the current turn's user message into memory so planners
    # never operate on a stale last_user_message from a prior turn.
    conversation_memory.last_user_message = user_message

    return AgentState(
        messages=[HumanMessage(content=user_message)],
        conversation_id=conversation_id,
        current_interaction=draft.to_serializable(),
        current_hcp=current_hcp.to_serializable() if current_hcp else None,
        selected_tool=None,
        tool_result=None,
        interaction_status="draft",
        user_context=context.to_serializable(),
        memory=conversation_memory.to_serializable(),
        validation_errors=[],
        response=None,
        planner_output=None,
        intent_output=None,
        router_output=None,
        validation_output=None,
        response_output=None,
        retry_count=0,
        error_message=None,
    )


def get_interaction_draft(state: AgentState) -> InteractionDraft:
    """Read the current interaction draft from graph state."""
    return InteractionDraft.from_serializable(state.get("current_interaction"))


def get_hcp_context(state: AgentState) -> HcpContext | None:
    """Read the current HCP context from graph state."""
    return HcpContext.from_serializable(state.get("current_hcp"))


def get_user_context(state: AgentState) -> UserContext:
    """Read user context from graph state."""
    return UserContext.from_serializable(state.get("user_context"))


def get_memory(state: AgentState) -> ConversationMemory:
    """Read conversation memory from graph state."""
    return ConversationMemory.from_serializable(state.get("memory"))


def serialize_planner_output(output: PlannerOutput) -> dict[str, Any]:
    return output.model_dump(mode="json")


def serialize_intent_output(output: IntentReasonerOutput) -> dict[str, Any]:
    return output.model_dump(mode="json")


def serialize_router_output(output: ToolRouterOutput) -> dict[str, Any]:
    return output.model_dump(mode="json")


def serialize_validation_output(output: ValidationOutput) -> dict[str, Any]:
    return output.model_dump(mode="json")


def serialize_response_output(output: ResponseGeneratorOutput) -> dict[str, Any]:
    return output.model_dump(mode="json")


def get_selected_tool_name(state: AgentState) -> ToolName | None:
    """Return the selected tool enum when available."""
    selected = state.get("selected_tool")
    if not selected:
        return None
    try:
        return ToolName(selected)
    except ValueError:
        return ToolName.NONE
