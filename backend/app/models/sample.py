"""Drug sample ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction_associations import InteractionSample
    from app.models.product import Product


class Sample(AuditMixin, Base):
    """Physical drug sample inventory available for distribution."""

    __tablename__ = "samples"
    __table_args__ = (
        Index("ix_samples_product_active", "product_id"),
        Index("ix_samples_lot_active", "lot_number"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False, default="unit")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    product: Mapped[Product] = relationship(back_populates="samples")
    interaction_samples: Mapped[list[InteractionSample]] = relationship(back_populates="sample")
