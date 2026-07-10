"""API response helpers."""

import time
from typing import Any

from fastapi import Request

from app.schemas.responses import ApiResponse, ResponseMeta


def build_meta(
    request: Request,
    *,
    execution_time_ms: float | None = None,
    selected_tool: str | None = None,
    conversation_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> ResponseMeta:
    """Build response metadata from request context."""
    meta = ResponseMeta(
        request_id=getattr(request.state, "request_id", None),
        correlation_id=getattr(request.state, "correlation_id", None),
        execution_time_ms=execution_time_ms,
        selected_tool=selected_tool,
        conversation_id=conversation_id,
    )
    if extra:
        meta_dict = meta.model_dump()
        meta_dict.update(extra)
        return ResponseMeta(**meta_dict)
    return meta


def success_response(
    *,
    request: Request,
    message: str,
    data: Any = None,
    execution_time_ms: float | None = None,
    selected_tool: str | None = None,
    conversation_id: str | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> ApiResponse[Any]:
    """Build a standard success API response."""
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        meta=build_meta(
            request,
            execution_time_ms=execution_time_ms,
            selected_tool=selected_tool,
            conversation_id=conversation_id,
            extra=extra_meta,
        ),
    )
