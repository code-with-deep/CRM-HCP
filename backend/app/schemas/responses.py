"""Standard API response envelope."""

from typing import Any, Generic, TypeVar

from pydantic import Field

from app.schemas.common import SchemaBase

DataT = TypeVar("DataT")


class ResponseMeta(SchemaBase):
    """Response metadata for tracing and pagination."""

    request_id: str | None = None
    correlation_id: str | None = None
    execution_time_ms: float | None = None
    selected_tool: str | None = None
    conversation_id: str | None = None


class ApiResponse(SchemaBase, Generic[DataT]):
    """Consistent API success/error response envelope."""

    success: bool = True
    message: str = "Request completed successfully."
    data: DataT | None = None
    errors: list[str] = Field(default_factory=list)
    meta: ResponseMeta | dict[str, Any] = Field(default_factory=ResponseMeta)


class ErrorDetail(SchemaBase):
    """Structured API error detail."""

    code: str
    message: str
    detail: str | list[Any] | dict[str, Any] | None = None


class ApiErrorResponse(SchemaBase):
    """Consistent API error response envelope."""

    success: bool = False
    message: str
    data: None = None
    errors: list[str] = Field(default_factory=list)
    meta: ResponseMeta | dict[str, Any] = Field(default_factory=ResponseMeta)
