"""Chat service orchestrating conversation persistence and LangGraph."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import get_logger
from app.langgraph.state import UserContext
from app.models.conversation import ConversationMessage, ConversationSession
from app.models.enums import ConversationSessionStatus, MessageRole
from app.repositories.conversation_repository import (
    ConversationMessageRepository,
    ConversationSessionRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.chat import ChatRequest, ChatResponseData, ConversationMessageItem
from app.services.agent_service import AgentService

logger = get_logger(__name__)


class ChatService:
    """Application service for AI chat routed exclusively through LangGraph."""

    def __init__(
        self,
        *,
        agent_service: AgentService,
        session_repository: ConversationSessionRepository,
        message_repository: ConversationMessageRepository,
        session: AsyncSession,
    ) -> None:
        self._agent_service = agent_service
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._session = session

    async def process_chat(
        self,
        request: ChatRequest,
        *,
        user_context: UserContext | None = None,
    ) -> tuple[ChatResponseData, float]:
        """Process a chat turn and persist conversation state."""
        start_time = time.perf_counter()
        await self._validate_user(request.user_id)
        conversation_session = await self._load_or_create_session(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        prior_messages = await self._load_prior_messages(conversation_session.id)
        session_state = self._load_session_state(conversation_session)

        current_interaction = request.current_interaction or session_state.get(
            "current_interaction",
            {},
        )
        current_hcp = request.current_hcp or session_state.get("current_hcp")
        memory = session_state.get("memory", {})

        context = user_context or UserContext(user_id=str(request.user_id))

        final_state = await self._agent_service.process_message(
            user_message=request.message,
            conversation_id=conversation_session.id,
            current_interaction=current_interaction,
            current_hcp=current_hcp,
            user_context=context,
            memory=memory,
            prior_messages=prior_messages,
        )

        payload = self._agent_service.build_chat_response(final_state)
        await self._persist_turn(
            conversation_session=conversation_session,
            user_message=request.message,
            payload=payload,
        )

        history = await self._build_conversation_history(conversation_session.id)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Chat completed conversation_id=%s selected_tool=%s execution_time_ms=%.2f",
            conversation_session.id,
            payload.get("selected_tool"),
            elapsed_ms,
        )

        response_data = ChatResponseData.from_agent_payload(
            payload,
            conversation_history=history,
        )
        return response_data, elapsed_ms

    async def get_session_state(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ChatResponseData:
        """Return persisted conversation state for client rehydration after refresh."""
        await self._validate_user(user_id)
        conversation_session = await self._session_repository.get_by_id(conversation_id)
        if conversation_session is None:
            raise NotFoundException(
                message="Conversation not found",
                detail=f"No conversation session exists for id={conversation_id}",
            )
        if conversation_session.user_id != user_id:
            raise NotFoundException(
                message="Conversation not found",
                detail=f"No conversation session exists for id={conversation_id}",
            )

        session_state = self._load_session_state(conversation_session)
        history = await self._build_conversation_history(conversation_session.id)
        payload = {
            "conversation_id": str(conversation_session.id),
            "interaction_patch": session_state.get("current_interaction", {}),
            "current_hcp": session_state.get("current_hcp"),
            "interaction_status": session_state.get("interaction_status", "draft"),
            "memory": session_state.get("memory", {}),
        }
        return ChatResponseData.from_agent_payload(
            payload,
            conversation_history=history,
        )

    async def stream_chat(
        self,
        request: ChatRequest,
        *,
        user_context: UserContext | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream LangGraph progress and assistant response as SSE events."""
        start_time = time.perf_counter()
        await self._validate_user(request.user_id)
        conversation_session = await self._load_or_create_session(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        prior_messages = await self._load_prior_messages(conversation_session.id)
        session_state = self._load_session_state(conversation_session)

        current_interaction = request.current_interaction or session_state.get(
            "current_interaction",
            {},
        )
        current_hcp = request.current_hcp or session_state.get("current_hcp")
        memory = session_state.get("memory", {})
        context = user_context or UserContext(user_id=str(request.user_id))

        yield {
            "event": "status",
            "data": {
                "message": "Conversation loaded. Invoking LangGraph agent.",
                "conversation_id": str(conversation_session.id),
            },
        }

        merged_state: dict[str, Any] = {
            "conversation_id": str(conversation_session.id),
            "current_interaction": current_interaction,
            "current_hcp": current_hcp,
            "interaction_status": session_state.get("interaction_status", "draft"),
        }
        async for update in self._agent_service.stream_message(
            user_message=request.message,
            conversation_id=conversation_session.id,
            current_interaction=current_interaction,
            current_hcp=current_hcp,
            user_context=context,
            memory=memory,
            prior_messages=prior_messages,
        ):
            for node_name, node_state in update.items():
                merged_state.update(node_state)
                yield {
                    "event": "status",
                    "data": {
                        "message": f"Completed node: {node_name}",
                        "node": node_name,
                        "selected_tool": merged_state.get("selected_tool"),
                        "interaction_status": merged_state.get("interaction_status"),
                    },
                }

        final_state = merged_state
        if not final_state.get("response"):
            yield {
                "event": "error",
                "data": {"message": "LangGraph did not return a final state."},
            }
            return

        payload = self._agent_service.build_chat_response(final_state)
        await self._persist_turn(
            conversation_session=conversation_session,
            user_message=request.message,
            payload=payload,
        )

        assistant_message = payload.get("assistant_message") or ""
        if assistant_message:
            for token in assistant_message.split():
                yield {"event": "token", "data": {"content": f"{token} "}}

        history = await self._build_conversation_history(conversation_session.id)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        response_data = ChatResponseData.from_agent_payload(
            payload,
            conversation_history=history,
        )

        logger.info(
            "Chat stream completed conversation_id=%s selected_tool=%s execution_time_ms=%.2f",
            conversation_session.id,
            payload.get("selected_tool"),
            elapsed_ms,
        )

        yield {
            "event": "complete",
            "data": {
                "response": response_data.model_dump(mode="json"),
                "execution_time_ms": elapsed_ms,
            },
        }

    async def _validate_user(self, user_id: UUID) -> None:
        """Ensure the requesting user exists before creating conversation state."""
        user_repository = UserRepository(self._session)
        user = await user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException(
                message="User not found",
                detail=(
                    f"No user exists for id={user_id}. "
                    "Run `python scripts/seed_database.py` from the backend directory."
                ),
            )
        if not user.is_active:
            raise ValidationException(
                message="User is inactive",
                detail=f"User id={user_id} is not active.",
            )

    async def _load_or_create_session(
        self,
        *,
        conversation_id: UUID | None,
        user_id: UUID,
    ) -> ConversationSession:
        """Load an existing conversation or create a new session."""
        if conversation_id:
            session = await self._session_repository.get_by_id(conversation_id)
            if session is None:
                raise NotFoundException(
                    message="Conversation not found",
                    detail=f"No conversation session exists for id={conversation_id}",
                )
            return session

        new_session = ConversationSession(
            id=uuid4(),
            user_id=user_id,
            status=ConversationSessionStatus.ACTIVE,
            started_at=datetime.now(UTC),
            session_metadata={},
            created_by=user_id,
        )
        return await self._session_repository.create(new_session)

    async def _load_prior_messages(self, session_id: UUID) -> list[HumanMessage | AIMessage]:
        """Rebuild LangChain messages from persisted conversation history."""
        messages_db = await self._message_repository.list_all_by_session(session_id)
        messages: list[HumanMessage | AIMessage] = []
        for message in messages_db:
            if message.role == MessageRole.USER:
                messages.append(HumanMessage(content=message.content))
            elif message.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=message.content))
        return messages

    async def _build_conversation_history(
        self,
        session_id: UUID,
    ) -> list[ConversationMessageItem]:
        """Return conversation history for API responses."""
        messages_db = await self._message_repository.list_all_by_session(session_id)
        return [
            ConversationMessageItem(
                role=message.role.value,
                content=message.content,
                tool_called=message.tool_called,
                sequence_number=message.sequence_number,
                timestamp=message.timestamp.isoformat() if message.timestamp else None,
            )
            for message in messages_db
        ]

    async def _persist_turn(
        self,
        *,
        conversation_session: ConversationSession,
        user_message: str,
        payload: dict[str, Any],
    ) -> None:
        """Persist user/assistant messages and updated session metadata."""
        user_sequence = await self._message_repository.get_next_sequence_number(
            conversation_session.id,
        )
        await self._message_repository.create(
            ConversationMessage(
                session_id=conversation_session.id,
                role=MessageRole.USER,
                content=user_message,
                sequence_number=user_sequence,
                created_by=conversation_session.user_id,
            ),
        )

        assistant_message = payload.get("assistant_message")
        if assistant_message:
            assistant_sequence = await self._message_repository.get_next_sequence_number(
                conversation_session.id,
            )
            await self._message_repository.create(
                ConversationMessage(
                    session_id=conversation_session.id,
                    role=MessageRole.ASSISTANT,
                    content=assistant_message,
                    tool_called=payload.get("selected_tool"),
                    sequence_number=assistant_sequence,
                    created_by=conversation_session.user_id,
                ),
            )

        conversation_session.session_metadata = {
            "current_interaction": payload.get("interaction_patch", {}),
            "current_hcp": payload.get("current_hcp"),
            "memory": payload.get("memory", {}),
            "interaction_status": payload.get("interaction_status", "draft"),
        }
        payload["conversation_id"] = str(conversation_session.id)
        await self._session_repository.update(conversation_session)
        await self._session.commit()

    @staticmethod
    def _load_session_state(session: ConversationSession) -> dict[str, Any]:
        """Read persisted conversation state from session metadata."""
        return session.session_metadata or {}
