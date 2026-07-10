"""FastAPI dependency injection providers (re-exported from core)."""

from app.core.dependencies import (  # noqa: F401
    AgentServiceDep,
    ChatServiceDep,
    CurrentUserDep,
    DbSessionDep,
    HcpServiceDep,
    InteractionServiceDep,
    SettingsDep,
    get_agent_service,
    get_current_user,
    get_db_session,
    get_settings_dependency,
)
