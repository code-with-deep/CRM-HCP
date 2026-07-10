"""Validation node for tool outputs."""

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName, ValidationOutput
from app.langgraph.state import AgentState, get_interaction_draft, serialize_validation_output
from app.langgraph.tools.date_utils import normalize_interaction_patch

logger = get_logger(__name__)


def _validate_tool_result(state: AgentState) -> ValidationOutput:
    """Deterministic validation — avoids an extra LLM round-trip for speed."""
    selected_tool = state.get("selected_tool") or "none"
    tool_result = state.get("tool_result") or {}
    draft = get_interaction_draft(state)

    if selected_tool in {ToolName.NONE.value, "none"}:
        return ValidationOutput(is_valid=True, normalized_result={})

    if not tool_result.get("success", True):
        return ValidationOutput(
            is_valid=False,
            errors=[tool_result.get("message") or "Tool execution failed."],
            should_retry=False,
        )

    patch = tool_result.get("interaction_patch") or {}
    if isinstance(patch, dict):
        patch = normalize_interaction_patch(patch)
        tool_result = {**tool_result, "interaction_patch": patch}

    errors: list[str] = []

    if selected_tool == ToolName.LOG_INTERACTION.value:
        merged = {**draft.to_serializable(), **(patch if isinstance(patch, dict) else {})}
        if not merged.get("hcp_name"):
            errors.append("HCP name is missing from the interaction draft.")
        if not merged.get("interaction_date"):
            errors.append("Interaction date is missing from the interaction draft.")

    if selected_tool == ToolName.SEARCH_HCP.value:
        hcp_context = tool_result.get("hcp_context")
        results = (tool_result.get("metadata") or {}).get("total_results")
        if not hcp_context and results == 0:
            errors.append("No matching HCP was found.")

    # Soft validation: keep going with warnings rather than retry loops.
    return ValidationOutput(
        is_valid=True,
        errors=errors,
        normalized_result=tool_result,
        should_retry=False,
    )


async def validation_node(state: AgentState) -> dict:
    """Validate tool output structure and business constraints without an LLM call."""
    validation_output = _validate_tool_result(state)
    logger.info(
        "Validation complete tool=%s valid=%s errors=%s",
        state.get("selected_tool"),
        validation_output.is_valid,
        validation_output.errors,
    )

    return {
        "validation_output": serialize_validation_output(validation_output),
        "validation_errors": validation_output.errors,
        "tool_result": (
            validation_output.normalized_result
            if validation_output.normalized_result
            else state.get("tool_result")
        ),
    }
