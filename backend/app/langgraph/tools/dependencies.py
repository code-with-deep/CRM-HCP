"""Dependency injection container for LangGraph tool execution."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.langgraph.llm import LLMService, get_llm_service
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.services.hcp_tool_service import HcpToolService
from app.services.interaction_tool_service import InteractionToolService


@dataclass(slots=True)
class ToolDependencies:
    """Dependencies injected into CRM LangGraph tools."""

    session: AsyncSession
    llm_service: LLMService
    hcp_tool_service: HcpToolService
    interaction_tool_service: InteractionToolService


def create_tool_dependencies(session: AsyncSession) -> ToolDependencies:
    """Build tool dependencies for a request-scoped database session."""
    hcp_repository = HcpRepository(session)
    interaction_repository = InteractionRepository(session)

    return ToolDependencies(
        session=session,
        llm_service=get_llm_service(),
        hcp_tool_service=HcpToolService(
            hcp_repository=hcp_repository,
            interaction_repository=interaction_repository,
        ),
        interaction_tool_service=InteractionToolService(
            interaction_repository=interaction_repository,
        ),
    )
