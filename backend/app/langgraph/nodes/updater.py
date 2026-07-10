"""State updater node."""

from typing import Any

from app.langgraph.schemas import ToolName
from app.langgraph.state import (
    AgentState,
    HcpContext,
    InteractionDraft,
    get_hcp_context,
    get_interaction_draft,
    get_selected_tool_name,
)


def _replace_interaction_draft(patch: dict[str, Any]) -> InteractionDraft:
    """Build a fresh interaction draft from a new log patch."""
    base = InteractionDraft().model_dump()
    list_fields = {
        "attendees",
        "topics_discussed",
        "materials_shared",
        "samples_distributed",
    }

    for field_name, value in patch.items():
        if field_name not in base or value is None:
            continue
        if field_name in list_fields and value == []:
            base[field_name] = []
        elif value != "":
            base[field_name] = value

    return InteractionDraft.model_validate(base)


def _merge_interaction_patch(
    draft: InteractionDraft,
    patch: dict[str, Any],
) -> InteractionDraft:
    """Merge a tool interaction patch into the current draft."""
    if not patch:
        return draft

    draft_data = draft.model_dump()
    list_fields = {
        "attendees",
        "topics_discussed",
        "materials_shared",
        "samples_distributed",
    }

    for field_name, value in patch.items():
        if field_name not in draft_data:
            continue
        if value is None:
            continue

        if field_name in list_fields and isinstance(value, list):
            if value == []:
                draft_data[field_name] = []
                continue
            existing = draft_data.get(field_name) or []
            merged = list(existing)
            for item in value:
                if item not in merged:
                    merged.append(item)
            draft_data[field_name] = merged
        elif value != "":
            draft_data[field_name] = value

    return InteractionDraft.model_validate(draft_data)


async def state_updater_node(state: AgentState) -> dict:
    """Update interaction draft, HCP context, and interaction status."""
    draft = get_interaction_draft(state)
    tool_result = state.get("tool_result") or {}
    selected_tool = get_selected_tool_name(state)
    hcp_context = get_hcp_context(state)

    patch = tool_result.get("interaction_patch", {})
    if isinstance(patch, dict) and patch:
        if selected_tool == ToolName.LOG_INTERACTION:
            draft = _replace_interaction_draft(patch)
        else:
            draft = _merge_interaction_patch(draft, patch)

    hcp_patch = tool_result.get("hcp_context")
    if isinstance(hcp_patch, dict) and hcp_patch:
        current_hcp = hcp_context.model_dump() if hcp_context else {}
        current_hcp.update({key: value for key, value in hcp_patch.items() if value is not None})
        hcp_context = HcpContext.model_validate(current_hcp)

    interaction_status = state.get("interaction_status", "draft")
    if selected_tool in {ToolName.LOG_INTERACTION, ToolName.EDIT_INTERACTION}:
        interaction_status = "draft"

    return {
        "current_interaction": draft.to_serializable(),
        "current_hcp": hcp_context.to_serializable() if hcp_context else None,
        "interaction_status": interaction_status,
    }
