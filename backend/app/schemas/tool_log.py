"""Tool execution log Pydantic schemas."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import ToolExecutionStatus
from app.schemas.common import AuditSchema, SchemaBase


class ToolExecutionLogBase(SchemaBase):
    """Shared tool execution log fields."""

    session_id: UUID | None = None
    message_id: UUID | None = None
    tool_name: str = Field(min_length=1, max_length=150)
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    execution_time_ms: int | None = Field(default=None, ge=0)
    status: ToolExecutionStatus
    error: str | None = None


class ToolExecutionLogCreate(ToolExecutionLogBase):
    """Schema for creating a tool execution log."""

    created_by: UUID | None = None


class ToolExecutionLogUpdate(SchemaBase):
    """Schema for updating a tool execution log."""

    output_payload: dict[str, Any] | None = None
    execution_time_ms: int | None = Field(default=None, ge=0)
    status: ToolExecutionStatus | None = None
    error: str | None = None
    updated_by: UUID | None = None


class ToolExecutionLogRead(ToolExecutionLogBase, AuditSchema):
    """Internal read schema for tool execution logs."""


class ToolExecutionLogResponse(ToolExecutionLogRead):
    """API response schema for tool execution logs."""
