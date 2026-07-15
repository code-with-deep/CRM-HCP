"""HCP interaction ORM model."""

from __future__ import annotations

import uuid
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import InteractionStatus, Sentiment
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.conversation import ConversationSession
    from app.models.hcp import Hcp
    from app.models.interaction_associations import (
        InteractionAttendee,
        InteractionMaterial,
        InteractionProduct,
        InteractionSample,
        InteractionTopic,
    )
    from app.models.interaction_type import InteractionType
    from app.models.user import User


class Interaction(AuditMixin, Base):
    """Primary record for a medical representative HCP interaction."""

    __tablename__ = "interactions"
    __table_args__ = (
        Index("ix_interactions_hcp_active", "hcp_id"),
        Index("ix_interactions_user_active", "user_id"),
        Index("ix_interactions_date_status_active", "interaction_date", "status"),
        Index("ix_interactions_conversation_active", "conversation_id"),
    )

    hcp_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("hcps.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    interaction_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("interaction_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    interaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    interaction_time: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[Sentiment | None] = mapped_column(
        Enum(Sentiment, name="sentiment", native_enum=False),
        nullable=True,
    )
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InteractionStatus] = mapped_column(
        Enum(InteractionStatus, name="interaction_status", native_enum=False),
        nullable=False,
        default=InteractionStatus.DRAFT,
    )

    hcp: Mapped[Hcp] = relationship(back_populates="interactions")
    user: Mapped[User] = relationship(back_populates="interactions", foreign_keys=[user_id])
    interaction_type: Mapped[InteractionType] = relationship(back_populates="interactions")
    conversation: Mapped[ConversationSession | None] = relationship(back_populates="interaction")
    attendees: Mapped[list[InteractionAttendee]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    topics: Mapped[list[InteractionTopic]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    materials: Mapped[list[InteractionMaterial]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    samples: Mapped[list[InteractionSample]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    products: Mapped[list[InteractionProduct]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
