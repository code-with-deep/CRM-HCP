"""Pharmaceutical product ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction_associations import InteractionProduct
    from app.models.material import Material
    from app.models.sample import Sample


class Product(AuditMixin, Base):
    """Marketable product promoted during HCP interactions."""

    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_name_brand_active", "product_name", "brand"),
        Index("ix_products_category_active", "category"),
    )

    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(150), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    materials: Mapped[list[Material]] = relationship(back_populates="product")
    samples: Mapped[list[Sample]] = relationship(back_populates="product")
    interaction_products: Mapped[list[InteractionProduct]] = relationship(back_populates="product")
