"""Interaction type lookup model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction import Interaction


class InteractionType(AuditMixin, Base):
    """Reference data for interaction channels such as calls or meetings."""

    __tablename__ = "interaction_types"
    __table_args__ = (
        Index(
            "ix_interaction_types_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    interactions: Mapped[list[Interaction]] = relationship(back_populates="interaction_type")
