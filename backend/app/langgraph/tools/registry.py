"""Dynamic LangGraph tool registry."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState
from app.langgraph.tools.base_tool import BaseCrmTool
from app.langgraph.tools.dependencies import ToolDependencies, create_tool_dependencies
from app.langgraph.tools.edit_interaction import edit_interaction_tool
from app.langgraph.tools.log_interaction import log_interaction_tool
from app.langgraph.tools.materials_samples import materials_and_samples_tool
from app.langgraph.tools.outcome_followup import outcome_and_followup_tool
from app.langgraph.tools.schemas import ToolExecutionResult
from app.langgraph.tools.search_hcp import search_hcp_tool

logger = get_logger(__name__)

ToolExecutor = Callable[
    [AgentState, dict[str, Any], ToolDependencies],
    Awaitable[ToolExecutionResult],
]


REGISTERED_TOOLS: list[BaseCrmTool] = [
    log_interaction_tool,
    edit_interaction_tool,
    search_hcp_tool,
    materials_and_samples_tool,
    outcome_and_followup_tool,
]

TOOL_REGISTRY: dict[ToolName, BaseCrmTool] = {tool.name: tool for tool in REGISTERED_TOOLS}


def register_tool(tool: BaseCrmTool) -> None:
    """Register a CRM tool dynamically."""
    TOOL_REGISTRY[tool.name] = tool
    if tool not in REGISTERED_TOOLS:
        REGISTERED_TOOLS.append(tool)
    logger.info("Registered LangGraph tool: %s", tool.name.value)


def get_tool(tool_name: ToolName) -> BaseCrmTool | None:
    """Return a registered CRM tool."""
    if tool_name == ToolName.NONE:
        return None
    return TOOL_REGISTRY.get(tool_name)


def get_tool_executor(tool_name: ToolName) -> ToolExecutor | None:
    """Return an async executor function for a registered tool."""
    tool = get_tool(tool_name)
    if tool is None:
        return None

    async def _execute(
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        return await tool.execute(
            state=state,
            tool_input=tool_input,
            dependencies=dependencies,
        )

    return _execute


def list_registered_tools() -> list[str]:
    """Return all registered tool names."""
    return [tool.name.value for tool in REGISTERED_TOOLS]


def list_langchain_tools() -> list:
    """Return LangChain StructuredTool wrappers for all registered tools."""
    return [tool.to_langchain_tool() for tool in REGISTERED_TOOLS]


__all__ = [
    "REGISTERED_TOOLS",
    "TOOL_REGISTRY",
    "ToolExecutionResult",
    "create_tool_dependencies",
    "get_tool",
    "get_tool_executor",
    "list_langchain_tools",
    "list_registered_tools",
    "register_tool",
]
