"""Tool executor node."""

from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState, get_selected_tool_name
from app.langgraph.tools.dependencies import create_tool_dependencies
from app.langgraph.tools.registry import ToolExecutionResult, get_tool_executor

logger = get_logger(__name__)


async def tool_executor_node(state: AgentState) -> dict:
    """Execute the LLM-selected tool without embedding business logic."""
    selected_tool = get_selected_tool_name(state)
    router_output = state.get("router_output") or {}
    tool_input = router_output.get("tool_input", {})

    if not selected_tool or selected_tool == ToolName.NONE:
        return {
            "tool_result": ToolExecutionResult(
                success=True,
                tool_name=ToolName.NONE.value,
                message="No tool execution required.",
            ).model_dump(mode="json"),
        }

    executor = get_tool_executor(selected_tool)
    if executor is None:
        logger.error("No executor registered for tool: %s", selected_tool.value)
        return {
            "tool_result": ToolExecutionResult(
                success=False,
                tool_name=selected_tool.value,
                message=f"No executor registered for tool '{selected_tool.value}'.",
            ).model_dump(mode="json"),
            "error_message": f"Unknown tool selected: {selected_tool.value}",
        }

    try:
        async with async_session_factory() as session:
            dependencies = create_tool_dependencies(session)
            result = await executor(state, tool_input, dependencies)
            await session.commit()
            return {
                "tool_result": result.model_dump(mode="json"),
                "error_message": None if result.success else result.message,
            }
    except Exception as exc:
        logger.error("Tool execution failed: %s", str(exc), exc_info=exc)
        return {
            "tool_result": ToolExecutionResult(
                success=False,
                tool_name=selected_tool.value,
                message=f"Tool execution failed: {exc}",
            ).model_dump(mode="json"),
            "error_message": f"Tool execution failed: {exc}",
        }
