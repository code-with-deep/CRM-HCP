"""Interaction persistence and retrieval endpoints."""

import time
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.response import success_response
from app.core.dependencies import CurrentUserDep, InteractionServiceDep
from app.schemas.interaction_api import SaveInteractionRequest
from app.schemas.interaction_detail import InteractionDetailResponse
from app.schemas.responses import ApiResponse

router = APIRouter(prefix="/interaction", tags=["Interactions"])


@router.post(
    "/save",
    response_model=ApiResponse[InteractionDetailResponse],
    summary="Persist an AI interaction draft",
    responses={
        200: {
            "description": "Saved interaction",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Interaction saved successfully.",
                        "data": {
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "hcp_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                            "status": "completed",
                        },
                        "errors": [],
                        "meta": {},
                    },
                },
            },
        },
    },
)
async def save_interaction(
    request: Request,
    payload: SaveInteractionRequest,
    interaction_service: InteractionServiceDep,
    current_user: CurrentUserDep,
) -> ApiResponse[InteractionDetailResponse]:
    """Validate and persist an interaction draft with related associations.

    The user_id in the payload is overridden by the verified JWT identity so that
    a user cannot save an interaction under another user's account.
    """
    start_time = time.perf_counter()
    enforced_payload = payload.model_copy(update={"user_id": UUID(current_user.user_id)})
    saved = await interaction_service.save_interaction(enforced_payload)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return success_response(
        request=request,
        message="Interaction saved successfully.",
        data=saved,
        execution_time_ms=elapsed_ms,
    )


@router.get(
    "/{interaction_id}",
    response_model=ApiResponse[InteractionDetailResponse],
    summary="Get a complete interaction",
)
async def get_interaction(
    request: Request,
    interaction_id: UUID,
    interaction_service: InteractionServiceDep,
    current_user: CurrentUserDep,
) -> ApiResponse[InteractionDetailResponse]:
    """Return a complete interaction with attendees, topics, materials, samples, and products.

    Medical representatives can only retrieve their own interactions.
    Managers and admins can retrieve any interaction.
    """
    start_time = time.perf_counter()
    interaction = await interaction_service.get_interaction(
        interaction_id,
        requesting_user_id=UUID(current_user.user_id),
        requesting_role=current_user.role,
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return success_response(
        request=request,
        message="Interaction retrieved successfully.",
        data=interaction,
        execution_time_ms=elapsed_ms,
    )
