"""Chat request and response schemas for LangGraph integration."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.langgraph.state import InteractionDraft
from app.schemas.common import SchemaBase


class ChatRequest(SchemaBase):
    """Incoming chat request routed to the LangGraph agent."""

    message: str = Field(
        min_length=1,
        description="User message to process through the LangGraph agent.",
        examples=["Log a meeting with Dr. Smith about CardioMax."],
    )
    conversation_id: UUID | None = Field(
        default=None,
        description="Existing conversation session identifier. Omit to start a new session.",
    )
    user_id: UUID = Field(description="CRM user initiating the conversation.")
    current_interaction: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional interaction draft override from the client.",
    )
    current_hcp: dict[str, Any] | None = Field(
        default=None,
        description="Optional HCP context override from the client.",
    )


class ConversationMessageItem(SchemaBase):
    """Single message in conversation history."""

    role: str
    content: str
    tool_called: str | None = None
    sequence_number: int
    timestamp: str | None = None


class ChatResponseData(SchemaBase):
    """Chat response payload produced by the LangGraph agent."""

    conversation_id: str
    assistant_message: str | None = None
    interaction_draft: dict[str, Any] = Field(default_factory=dict)
    current_hcp: dict[str, Any] | None = None
    interaction_status: str = "draft"
    conversation_history: list[ConversationMessageItem] = Field(default_factory=list)
    selected_tool: str | None = None
    tool_result: dict[str, Any] | None = None
    validation_errors: list[str] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None

    @classmethod
    def from_agent_payload(
        cls,
        payload: dict[str, Any],
        *,
        conversation_history: list[ConversationMessageItem] | None = None,
    ) -> "ChatResponseData":
        """Create a response schema from AgentService output."""
        interaction_draft = payload.get("interaction_patch") or InteractionDraft().to_serializable()
        return cls(
            conversation_id=str(payload.get("conversation_id")),
            assistant_message=payload.get("assistant_message"),
            interaction_draft=interaction_draft,
            current_hcp=payload.get("current_hcp"),
            interaction_status=payload.get("interaction_status") or "draft",
            conversation_history=conversation_history or [],
            selected_tool=payload.get("selected_tool"),
            tool_result=payload.get("tool_result"),
            validation_errors=payload.get("validation_errors", []),
            suggested_prompts=payload.get("suggested_prompts", []),
            memory=payload.get("memory", {}),
            error_message=payload.get("error_message"),
        )


class StreamEvent(SchemaBase):
    """Server-sent event payload for progressive chat responses."""

    event: str = Field(description="Event type: status, token, complete, error.")
    data: dict[str, Any] = Field(default_factory=dict)

