"""Service layer package exports."""

__all__ = [
    "AgentService",
    "CatalogService",
    "ChatService",
    "ConversationService",
    "HealthService",
    "HcpService",
    "HcpToolService",
    "InteractionService",
    "InteractionToolService",
    "ToolLogService",
    "UserService",
]


def __getattr__(name: str):
    """Lazily import services to avoid circular dependencies during tool loading."""
    if name == "AgentService":
        from app.services.agent_service import AgentService

        return AgentService
    if name == "CatalogService":
        from app.services.catalog_service import CatalogService

        return CatalogService
    if name == "ChatService":
        from app.services.chat_service import ChatService

        return ChatService
    if name == "ConversationService":
        from app.services.conversation_service import ConversationService

        return ConversationService
    if name == "HealthService":
        from app.services.health_service import HealthService

        return HealthService
    if name == "HcpService":
        from app.services.hcp_service import HcpService

        return HcpService
    if name == "HcpToolService":
        from app.services.hcp_tool_service import HcpToolService

        return HcpToolService
    if name == "InteractionService":
        from app.services.interaction_service import InteractionService

        return InteractionService
    if name == "InteractionToolService":
        from app.services.interaction_tool_service import InteractionToolService

        return InteractionToolService
    if name == "ToolLogService":
        from app.services.tool_log_service import ToolLogService

        return ToolLogService
    if name == "UserService":
        from app.services.user_service import UserService

        return UserService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
