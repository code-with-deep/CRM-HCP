"""Conversation memory helpers for LangGraph state."""

import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.langgraph.state import (
    AgentState,
    ConversationMemory,
    InteractionDraft,
    get_interaction_draft,
    get_memory,
)


def build_memory_summary(state: AgentState) -> str:
    """Create a compact memory summary for LLM nodes."""
    memory = get_memory(state)
    draft = get_interaction_draft(state)

    populated_fields = [
        field_name
        for field_name, value in draft.model_dump().items()
        if value not in (None, "", [], {})
    ]

    summary_parts = [
        f"turn_count={memory.turn_count}",
        f"last_user_message={memory.last_user_message or 'none'}",
        f"last_assistant_message={memory.last_assistant_message or 'none'}",
        f"last_tool_name={memory.last_tool_name or 'none'}",
        f"populated_interaction_fields={', '.join(populated_fields) or 'none'}",
        f"remembered_fields={', '.join(memory.remembered_fields) or 'none'}",
    ]

    if memory.interaction_history_summary:
        summary_parts.append(
            f"interaction_history_summary={memory.interaction_history_summary}",
        )

    return " | ".join(summary_parts)


def serialize_messages_for_prompt(messages: list[BaseMessage], limit: int = 8) -> str:
    """Serialize recent messages for LLM context windows."""
    recent_messages = messages[-limit:]
    serialized: list[dict[str, str]] = []

    for message in recent_messages:
        role = "user"
        if isinstance(message, AIMessage):
            role = "assistant"
        elif message.type:
            role = message.type

        content = message.content
        if not isinstance(content, str):
            content = json.dumps(content)

        serialized.append({"role": role, "content": content})

    return json.dumps(serialized, ensure_ascii=True)


def extract_latest_user_message(messages: list[BaseMessage]) -> str | None:
    """Return the most recent human message content."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            return content if isinstance(content, str) else str(content)
    return None


def update_memory_after_turn(
    *,
    state: AgentState,
    assistant_response: str,
    selected_tool: str | None = None,
    updated_draft: InteractionDraft | None = None,
) -> dict[str, Any]:
    """Update conversation memory after a completed graph turn."""
    memory = get_memory(state)
    user_message = extract_latest_user_message(state.get("messages", []))
    draft = updated_draft or get_interaction_draft(state)

    remembered_fields = [
        field_name
        for field_name, value in draft.model_dump().items()
        if value not in (None, "", [], {})
    ]

    updated_memory = ConversationMemory(
        turn_count=memory.turn_count + 1,
        last_user_message=user_message,
        last_assistant_message=assistant_response,
        last_tool_name=selected_tool or memory.last_tool_name,
        interaction_history_summary=build_interaction_history_summary(draft),
        remembered_fields=remembered_fields,
    )
    return updated_memory.to_serializable()


def build_interaction_history_summary(draft: InteractionDraft) -> str:
    """Summarize the current interaction draft for memory retention."""
    parts: list[str] = []

    if draft.hcp_name:
        parts.append(f"HCP={draft.hcp_name}")
    if draft.interaction_type:
        parts.append(f"Type={draft.interaction_type}")
    if draft.interaction_date:
        parts.append(f"Date={draft.interaction_date}")
    if draft.sentiment:
        parts.append(f"Sentiment={draft.sentiment}")
    if draft.topics_discussed:
        parts.append(f"Topics={', '.join(draft.topics_discussed)}")
    if draft.materials_shared:
        parts.append(f"Materials={', '.join(draft.materials_shared)}")
    if draft.samples_distributed:
        parts.append(f"Samples={', '.join(draft.samples_distributed)}")
    if draft.outcomes:
        parts.append(f"Outcomes={draft.outcomes}")
    if draft.follow_up_actions:
        parts.append(f"FollowUp={draft.follow_up_actions}")

    return " | ".join(parts) if parts else "No interaction details captured yet."
