"""Conditional routing helpers for the LangGraph agent."""

from typing import Literal

from app.config.settings import get_settings
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState


def route_after_router(state: AgentState) -> Literal["tool_executor", "response_generator"]:
    """Route to tool execution or direct response generation."""
    router_output = state.get("router_output") or {}
    selected_tool = state.get("selected_tool")

    if router_output.get("should_execute_tool") is False:
        return "response_generator"
    if not selected_tool or selected_tool == ToolName.NONE.value:
        return "response_generator"
    return "tool_executor"


def route_after_validation(
    state: AgentState,
) -> Literal["intent_reasoner", "state_updater"]:
    """Retry reasoning when validation fails, otherwise update state."""
    validation_output = state.get("validation_output") or {}
    settings = get_settings()

    if validation_output.get("is_valid", False):
        return "state_updater"

    retry_count = state.get("retry_count", 0)
    should_retry = validation_output.get("should_retry", False)
    if should_retry and retry_count < settings.LLM_MAX_VALIDATION_RETRIES:
        return "intent_reasoner"

    return "state_updater"
