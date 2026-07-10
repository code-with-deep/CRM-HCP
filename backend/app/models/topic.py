"""Discussion topic reference model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction_associations import InteractionTopic


class Topic(AuditMixin, Base):
    """Normalized topic catalog used during HCP interactions."""

    __tablename__ = "topics"
    __table_args__ = (
        Index(
            "ix_topics_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_topics_category_active", "category", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    interaction_topics: Mapped[list[InteractionTopic]] = relationship(back_populates="topic")
