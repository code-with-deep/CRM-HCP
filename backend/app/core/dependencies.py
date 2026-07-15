"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.database.session import get_db
from app.langgraph.state import UserContext
from app.models.enums import UserRole
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
from app.repositories.user_repository import UserRepository
from app.services.agent_service import AgentService
from app.services.chat_service import ChatService
from app.services.hcp_service import HcpService
from app.services.interaction_service import InteractionService

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=True)


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
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserContext:
    """Validate the Bearer JWT and return the authenticated user context."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if not user_id or not role:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await UserRepository(session).get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserContext(user_id=user_id, role=role)


def require_roles(*allowed_roles: UserRole) -> Depends:
    """Return a FastAPI dependency that enforces role-based access control.

    Usage:
        @router.get("/admin/data", dependencies=[require_roles(UserRole.ADMIN)])
    """
    async def _check(current_user: Annotated[UserContext, Depends(get_current_user)]) -> UserContext:
        if current_user.role not in {r.value for r in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in allowed_roles]}.",
            )
        return current_user

    return Depends(_check)


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
