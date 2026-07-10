"""LangGraph tool execution audit log model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ToolExecutionStatus
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.conversation import ConversationMessage, ConversationSession


class ToolExecutionLog(AuditMixin, Base):
    """Audit trail for LangGraph tool invocations."""

    __tablename__ = "tool_execution_logs"
    __table_args__ = (
        Index("ix_tool_execution_logs_session", "session_id"),
        Index("ix_tool_execution_logs_tool_name", "tool_name"),
        Index("ix_tool_execution_logs_status", "status"),
    )

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(150), nullable=False)
    input_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ToolExecutionStatus] = mapped_column(
        Enum(ToolExecutionStatus, name="tool_execution_status", native_enum=False),
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[ConversationSession | None] = relationship(back_populates="tool_logs")
    message: Mapped[ConversationMessage | None] = relationship(back_populates="tool_logs")
