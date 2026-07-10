"""Tool execution log service skeleton."""

from app.repositories.tool_log_repository import ToolExecutionLogRepository


class ToolLogService:
    """Application service for LangGraph tool execution auditing."""

    def __init__(self, tool_log_repository: ToolExecutionLogRepository) -> None:
        self._tool_log_repository = tool_log_repository
