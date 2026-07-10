"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.core.logging import get_logger
from app.database.session import get_db
from app.langgraph.state import UserContext
from app.repositories.conversation_repository import (
    ConversationMessageRepository,
    ConversationSessionRepository,
)
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_association_repository import (
    InteractionAttendeeRepository,
    InteractionMaterialRepository,
    InteractionProductRepository,
    InteractionSampleRepository,
    InteractionTopicRepository,
)
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.interaction_type_repository import InteractionTypeRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sample_repository import SampleRepository
from app.repositories.topic_repository import TopicRepository
from app.services.agent_service import AgentService
from app.services.chat_service import ChatService
from app.services.hcp_service import HcpService
from app.services.interaction_service import InteractionService

logger = get_logger(__name__)


def get_settings_dependency() -> Settings:
    """Inject application settings."""
    return get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Inject an async database session."""
    async for session in get_db():
        yield session


def get_agent_service() -> AgentService:
    """Inject the LangGraph agent orchestrator."""
    return AgentService()


async def get_current_user(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> UserContext:
    """Placeholder authentication dependency for future JWT integration."""
    if x_user_id:
        return UserContext(user_id=x_user_id, role="medical_representative")

    logger.debug("No X-User-Id header supplied; using unauthenticated placeholder context.")
    return UserContext(user_id=None, role="medical_representative")


def get_chat_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> ChatService:
    """Inject the chat service with repositories and LangGraph agent."""
    return ChatService(
        agent_service=agent_service,
        session_repository=ConversationSessionRepository(session),
        message_repository=ConversationMessageRepository(session),
        session=session,
    )


def get_interaction_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InteractionService:
    """Inject the interaction persistence service."""
    return InteractionService(
        interaction_repository=InteractionRepository(session),
        attendee_repository=InteractionAttendeeRepository(session),
        topic_repository=InteractionTopicRepository(session),
        material_repository=InteractionMaterialRepository(session),
        sample_repository=InteractionSampleRepository(session),
        product_repository=InteractionProductRepository(session),
        interaction_type_repository=InteractionTypeRepository(session),
        hcp_repository=HcpRepository(session),
        topic_catalog_repository=TopicRepository(session),
        material_catalog_repository=MaterialRepository(session),
        sample_catalog_repository=SampleRepository(session),
        product_catalog_repository=ProductRepository(session),
        session=session,
    )


def get_hcp_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HcpService:
    """Inject the HCP query service."""
    return HcpService(
        hcp_repository=HcpRepository(session),
        interaction_repository=InteractionRepository(session),
    )


SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[UserContext, Depends(get_current_user)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
InteractionServiceDep = Annotated[InteractionService, Depends(get_interaction_service)]
HcpServiceDep = Annotated[HcpService, Depends(get_hcp_service)]
