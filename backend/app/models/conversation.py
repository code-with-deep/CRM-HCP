"""AI conversation session and message models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ConversationSessionStatus, MessageRole
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction import Interaction
    from app.models.tool_log import ToolExecutionLog
    from app.models.user import User


class ConversationSession(AuditMixin, Base):
    """AI assistant conversation session linked to an interaction draft."""

    __tablename__ = "conversation_sessions"
    __table_args__ = (
        Index("ix_conversation_sessions_user_active", "user_id", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_conversation_sessions_status_active", "status", postgresql_where=text("deleted_at IS NULL")),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ConversationSessionStatus] = mapped_column(
        Enum(ConversationSessionStatus, name="conversation_session_status", native_enum=False),
        nullable=False,
        default=ConversationSessionStatus.ACTIVE,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(
        back_populates="conversation_sessions",
        foreign_keys=[user_id],
    )
    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.sequence_number",
    )
    interaction: Mapped[Interaction | None] = relationship(back_populates="conversation")
    tool_logs: Mapped[list[ToolExecutionLog]] = relationship(back_populates="session")


class ConversationMessage(AuditMixin, Base):
    """Single message within an AI conversation session."""

    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_session_sequence", "session_id", "sequence_number"),
        Index("ix_conversation_messages_role", "role"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", native_enum=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    tool_called: Mapped[str | None] = mapped_column(String(150), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    session: Mapped[ConversationSession] = relationship(back_populates="messages")
    tool_logs: Mapped[list[ToolExecutionLog]] = relationship(back_populates="message")
