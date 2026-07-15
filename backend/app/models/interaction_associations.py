"""Interaction association and junction tables."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.hcp import Hcp
    from app.models.interaction import Interaction
    from app.models.material import Material
    from app.models.product import Product
    from app.models.sample import Sample
    from app.models.topic import Topic


class InteractionAttendee(AuditMixin, Base):
    """Attendee participating in an HCP interaction."""

    __tablename__ = "interaction_attendees"
    __table_args__ = (
        Index("ix_interaction_attendees_interaction", "interaction_id"),
        Index("ix_interaction_attendees_hcp", "hcp_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    attendee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    attendee_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hcp_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("hcps.id", ondelete="SET NULL"),
        nullable=True,
    )

    interaction: Mapped[Interaction] = relationship(back_populates="attendees")
    hcp: Mapped[Hcp | None] = relationship(back_populates="attendee_records")


class InteractionTopic(AuditMixin, Base):
    """Many-to-many association between interactions and topics."""

    __tablename__ = "interaction_topics"
    __table_args__ = (
        UniqueConstraint("interaction_id", "topic_id", name="uq_interaction_topics_pair"),
        Index("ix_interaction_topics_interaction", "interaction_id"),
        Index("ix_interaction_topics_topic", "topic_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("topics.id", ondelete="RESTRICT"),
        nullable=False,
    )
    discussion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    interaction: Mapped[Interaction] = relationship(back_populates="topics")
    topic: Mapped[Topic] = relationship(back_populates="interaction_topics")


class InteractionMaterial(AuditMixin, Base):
    """Many-to-many association between interactions and materials."""

    __tablename__ = "interaction_materials"
    __table_args__ = (
        UniqueConstraint("interaction_id", "material_id", name="uq_interaction_materials_pair"),
        Index("ix_interaction_materials_interaction", "interaction_id"),
        Index("ix_interaction_materials_material", "material_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("materials.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_shared: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    interaction: Mapped[Interaction] = relationship(back_populates="materials")
    material: Mapped[Material] = relationship(back_populates="interaction_materials")


class InteractionSample(AuditMixin, Base):
    """Many-to-many association between interactions and distributed samples."""

    __tablename__ = "interaction_samples"
    __table_args__ = (
        UniqueConstraint("interaction_id", "sample_id", name="uq_interaction_samples_pair"),
        Index("ix_interaction_samples_interaction", "interaction_id"),
        Index("ix_interaction_samples_sample", "sample_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("samples.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_distributed: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    interaction: Mapped[Interaction] = relationship(back_populates="samples")
    sample: Mapped[Sample] = relationship(back_populates="interaction_samples")


class InteractionProduct(AuditMixin, Base):
    """Many-to-many association between interactions and discussed products."""

    __tablename__ = "interaction_products"
    __table_args__ = (
        UniqueConstraint("interaction_id", "product_id", name="uq_interaction_products_pair"),
        Index("ix_interaction_products_interaction", "interaction_id"),
        Index("ix_interaction_products_product", "product_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    interaction: Mapped[Interaction] = relationship(back_populates="products")
    product: Mapped[Product] = relationship(back_populates="interaction_products")
