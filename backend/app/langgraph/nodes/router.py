"""LLM-driven tool router node (derives from planner orchestration)."""

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName, ToolRouterOutput
from app.langgraph.state import AgentState, serialize_router_output

logger = get_logger(__name__)


def _resolve_tool_name(raw: str | None) -> ToolName:
    """Parse a tool name from planner output with a safe default."""
    if not raw:
        return ToolName.NONE
    try:
        return ToolName(raw)
    except ValueError:
        return ToolName.NONE


async def tool_router_node(state: AgentState) -> dict:
    """Select the tool from planner orchestration output (no extra LLM call)."""
    planner_output = state.get("planner_output") or {}
    intent_output = state.get("intent_output") or {}

    try:
        selected_tool = _resolve_tool_name(planner_output.get("selected_tool"))
        should_execute = bool(
            planner_output.get(
                "should_execute_tool",
                planner_output.get("requires_tool_execution", False),
            )
        )

        # If planner said tools are required but left selected_tool empty, map intent.
        if should_execute and selected_tool == ToolName.NONE:
            intent_to_tool = {
                "log_interaction": ToolName.LOG_INTERACTION,
                "edit_interaction": ToolName.EDIT_INTERACTION,
                "search_hcp": ToolName.SEARCH_HCP,
                "update_materials": ToolName.MATERIALS_AND_SAMPLES,
                "update_samples": ToolName.MATERIALS_AND_SAMPLES,
                "update_outcomes": ToolName.OUTCOME_AND_FOLLOWUP,
                "update_follow_up": ToolName.OUTCOME_AND_FOLLOWUP,
            }
            primary = intent_output.get("primary_intent") or planner_output.get("primary_intent")
            selected_tool = intent_to_tool.get(primary, ToolName.NONE)

        if intent_output.get("requires_clarification") and selected_tool == ToolName.NONE:
            should_execute = False

        if not should_execute:
            selected_tool = ToolName.NONE

        tool_input_raw = planner_output.get("tool_input") or {}
        if isinstance(tool_input_raw, dict):
            tool_input = dict(tool_input_raw)
        else:
            tool_input = {}

        # Map search alias if planner used doctor_name.
        if tool_input.get("doctor_name") and not tool_input.get("hcp_name"):
            tool_input["hcp_name"] = tool_input["doctor_name"]

        # Ensure the latest user message is available to tools.
        if not tool_input.get("user_instruction"):
            memory = state.get("memory") or {}
            last_user = memory.get("last_user_message")
            if last_user:
                tool_input["user_instruction"] = last_user

        router_output = ToolRouterOutput(
            selected_tool=selected_tool,
            tool_input=tool_input,
            routing_reasoning=planner_output.get("routing_reasoning")
            or planner_output.get("reasoning")
            or "Derived from planner orchestration.",
            should_execute_tool=should_execute and selected_tool != ToolName.NONE,
        )

        selected_value = (
            router_output.selected_tool.value
            if router_output.should_execute_tool
            else ToolName.NONE.value
        )

        logger.info(
            "Router derived from planner selected_tool=%s should_execute=%s",
            selected_value,
            router_output.should_execute_tool,
        )

        return {
            "router_output": serialize_router_output(router_output),
            "selected_tool": selected_value,
            "error_message": None,
        }
    except Exception as exc:
        logger.error("Tool router node failed: %s", str(exc), exc_info=exc)
        return {
            "router_output": ToolRouterOutput(
                selected_tool=ToolName.NONE,
                routing_reasoning="Tool routing failed while deriving planner output.",
                should_execute_tool=False,
            ).model_dump(mode="json"),
            "selected_tool": ToolName.NONE.value,
            "error_message": f"Tool router node failed: {exc}",
        }
