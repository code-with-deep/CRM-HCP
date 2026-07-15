"""Primary AI chat endpoints routed through LangGraph."""

import json
import time
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.response import success_response
from app.core.dependencies import ChatServiceDep, CurrentUserDep
from app.schemas.chat import ChatRequest, ChatResponseData
from app.schemas.responses import ApiResponse

router = APIRouter(tags=["Chat"])


@router.get(
    "/chat/session/{conversation_id}",
    response_model=ApiResponse[ChatResponseData],
    summary="Restore a persisted conversation session",
)
async def get_chat_session(
    request: Request,
    conversation_id: UUID,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
) -> ApiResponse[ChatResponseData]:
    """Return saved interaction draft, HCP context, and chat history for page reload.

    The user identity is taken exclusively from the verified JWT token —
    the caller cannot impersonate another user by supplying a different user_id.
    """
    start_time = time.perf_counter()
    response_data = await chat_service.get_session_state(
        conversation_id=conversation_id,
        user_id=UUID(current_user.user_id),
    )
    return success_response(
        request=request,
        message="Conversation session restored successfully.",
        data=response_data,
        execution_time_ms=(time.perf_counter() - start_time) * 1000,
        conversation_id=response_data.conversation_id,
    )


@router.post(
    "/chat",
    response_model=ApiResponse[ChatResponseData],
    summary="Process a chat message through LangGraph",
    responses={
        200: {
            "description": "Successful chat response",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Chat processed successfully.",
                        "data": {
                            "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "assistant_message": "I've updated the interaction draft for Dr. Smith.",
                            "interaction_draft": {
                                "hcp_name": "Dr. Jane Smith",
                                "interaction_type": "Meeting",
                                "interaction_date": "2026-07-09",
                            },
                            "interaction_status": "draft",
                            "conversation_history": [],
                            "selected_tool": "log_interaction",
                        },
                        "errors": [],
                        "meta": {"execution_time_ms": 1250.5},
                    },
                },
            },
        },
    },
)
async def chat(
    request: Request,
    payload: ChatRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
) -> ApiResponse[ChatResponseData]:
    """Route a user message through LangGraph and return the updated conversation state.

    The user_id in the payload is overridden by the verified JWT identity so that
    a user cannot create or read conversations belonging to another user.
    """
    start_time = time.perf_counter()
    enforced_payload = payload.model_copy(update={"user_id": UUID(current_user.user_id)})
    response_data, elapsed_ms = await chat_service.process_chat(
        enforced_payload, user_context=current_user
    )
    return success_response(
        request=request,
        message="Chat processed successfully.",
        data=response_data,
        execution_time_ms=elapsed_ms or ((time.perf_counter() - start_time) * 1000),
        selected_tool=response_data.selected_tool,
        conversation_id=response_data.conversation_id,
    )


@router.post(
    "/chat/stream",
    summary="Stream a chat response via Server-Sent Events",
    responses={
        200: {
            "description": "SSE stream of chat events",
            "content": {"text/event-stream": {}},
        },
    },
)
async def chat_stream(
    payload: ChatRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
) -> StreamingResponse:
    """Stream LangGraph progress and assistant response tokens via SSE.

    The user_id in the payload is overridden by the verified JWT identity.
    """
    enforced_payload = payload.model_copy(update={"user_id": UUID(current_user.user_id)})

    async def event_generator() -> AsyncIterator[str]:
        async for event in chat_service.stream_chat(enforced_payload, user_context=current_user):
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
