"""Agent service for invoking the LangGraph workflow from FastAPI."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph

from app.core.exceptions import LangGraphException, LLMTimeoutException
from app.core.logging import get_logger
from app.langgraph.state import (
    AgentState,
    ConversationMemory,
    HcpContext,
    InteractionDraft,
    UserContext,
    create_initial_state,
    get_interaction_draft,
)

logger = get_logger(__name__)


class AgentService:
    """Application service that routes all AI requests through LangGraph."""

    def __init__(self, graph: CompiledStateGraph | None = None) -> None:
        self._graph = graph

    @property
    def graph(self) -> CompiledStateGraph:
        """Lazily load the compiled LangGraph agent."""
        if self._graph is None:
            from app.langgraph.graph import get_agent_graph

            self._graph = get_agent_graph()
        return self._graph

    async def process_message(
        self,
        *,
        user_message: str,
        conversation_id: UUID | str | None = None,
        current_interaction: InteractionDraft | dict[str, Any] | None = None,
        current_hcp: HcpContext | dict[str, Any] | None = None,
        user_context: UserContext | dict[str, Any] | None = None,
        memory: ConversationMemory | dict[str, Any] | None = None,
        prior_messages: list[BaseMessage] | None = None,
    ) -> AgentState:
        """Process a user message through the LangGraph agent."""
        initial_state = self._build_initial_state(
            user_message=user_message,
            conversation_id=conversation_id,
            current_interaction=current_interaction,
            current_hcp=current_hcp,
            user_context=user_context,
            memory=memory,
            prior_messages=prior_messages,
        )

        logger.info(
            "Invoking LangGraph agent for conversation_id=%s",
            initial_state.get("conversation_id"),
        )

        try:
            final_state = await self.graph.ainvoke(initial_state)
        except TimeoutError as exc:
            logger.error("LLM timeout during LangGraph execution: %s", str(exc))
            raise LLMTimeoutException(detail=str(exc)) from exc
        except asyncio.TimeoutError as exc:
            logger.error("Async timeout during LangGraph execution: %s", str(exc))
            raise LLMTimeoutException(detail=str(exc)) from exc
        except Exception as exc:
            logger.error("LangGraph execution failed: %s", str(exc), exc_info=exc)
            raise LangGraphException(detail=str(exc)) from exc

        return final_state

    async def stream_message(
        self,
        *,
        user_message: str,
        conversation_id: UUID | str | None = None,
        current_interaction: InteractionDraft | dict[str, Any] | None = None,
        current_hcp: HcpContext | dict[str, Any] | None = None,
        user_context: UserContext | dict[str, Any] | None = None,
        memory: ConversationMemory | dict[str, Any] | None = None,
        prior_messages: list[BaseMessage] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream LangGraph node updates for progressive client responses."""
        initial_state = self._build_initial_state(
            user_message=user_message,
            conversation_id=conversation_id,
            current_interaction=current_interaction,
            current_hcp=current_hcp,
            user_context=user_context,
            memory=memory,
            prior_messages=prior_messages,
        )

        logger.info(
            "Streaming LangGraph agent for conversation_id=%s",
            initial_state.get("conversation_id"),
        )

        try:
            async for event in self.graph.astream(initial_state, stream_mode="updates"):
                yield event
        except TimeoutError as exc:
            logger.error("LLM timeout during LangGraph streaming: %s", str(exc))
            raise LLMTimeoutException(detail=str(exc)) from exc
        except asyncio.TimeoutError as exc:
            logger.error("Async timeout during LangGraph streaming: %s", str(exc))
            raise LLMTimeoutException(detail=str(exc)) from exc
        except Exception as exc:
            logger.error("LangGraph streaming failed: %s", str(exc), exc_info=exc)
            raise LangGraphException(detail=str(exc)) from exc

    def build_chat_response(self, final_state: AgentState) -> dict[str, Any]:
        """Map graph output to a FastAPI-friendly response payload."""
        draft = get_interaction_draft(final_state)
        response_output = final_state.get("response_output") or {}

        return {
            "conversation_id": final_state.get("conversation_id"),
            "assistant_message": final_state.get("response"),
            "interaction_patch": draft.to_serializable(),
            "current_hcp": final_state.get("current_hcp"),
            "interaction_status": final_state.get("interaction_status") or "draft",
            "selected_tool": final_state.get("selected_tool"),
            "tool_result": final_state.get("tool_result"),
            "validation_errors": final_state.get("validation_errors", []),
            "suggested_prompts": response_output.get("suggested_prompts", []),
            "memory": final_state.get("memory"),
            "error_message": final_state.get("error_message"),
        }

    def _build_initial_state(
        self,
        *,
        user_message: str,
        conversation_id: UUID | str | None,
        current_interaction: InteractionDraft | dict[str, Any] | None,
        current_hcp: HcpContext | dict[str, Any] | None,
        user_context: UserContext | dict[str, Any] | None,
        memory: ConversationMemory | dict[str, Any] | None,
        prior_messages: list[BaseMessage] | None,
    ) -> AgentState:
        """Build the initial graph state for invoke/stream operations."""
        interaction = self._coerce_interaction_draft(current_interaction)
        hcp = self._coerce_hcp_context(current_hcp)
        context = self._coerce_user_context(user_context)
        conversation_memory = self._coerce_memory(memory)

        initial_state = create_initial_state(
            user_message=user_message,
            conversation_id=str(conversation_id) if conversation_id else None,
            current_interaction=interaction,
            current_hcp=hcp,
            user_context=context,
            memory=conversation_memory,
        )

        if prior_messages:
            initial_state["messages"] = prior_messages + initial_state["messages"]

        return initial_state

    @staticmethod
    def _coerce_interaction_draft(
        value: InteractionDraft | dict[str, Any] | None,
    ) -> InteractionDraft:
        if isinstance(value, InteractionDraft):
            return value
        if isinstance(value, dict):
            return InteractionDraft.from_serializable(value)
        return InteractionDraft()

    @staticmethod
    def _coerce_hcp_context(value: HcpContext | dict[str, Any] | None) -> HcpContext | None:
        if isinstance(value, HcpContext):
            return value
        if isinstance(value, dict):
            return HcpContext.from_serializable(value)
        return None

    @staticmethod
    def _coerce_user_context(value: UserContext | dict[str, Any] | None) -> UserContext:
        if isinstance(value, UserContext):
            return value
        if isinstance(value, dict):
            return UserContext.from_serializable(value)
        return UserContext()

    @staticmethod
    def _coerce_memory(value: ConversationMemory | dict[str, Any] | None) -> ConversationMemory:
        if isinstance(value, ConversationMemory):
            return value
        if isinstance(value, dict):
            return ConversationMemory.from_serializable(value)
        return ConversationMemory()
