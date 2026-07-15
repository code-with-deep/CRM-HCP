"""Promotional material ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import MaterialType
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction_associations import InteractionMaterial
    from app.models.product import Product


class Material(AuditMixin, Base):
    """Educational or promotional material shared with HCPs."""

    __tablename__ = "materials"
    __table_args__ = (
        Index("ix_materials_type_active", "material_type"),
        Index("ix_materials_product_active", "product_id"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    material_type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType, name="material_type", native_enum=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product: Mapped[Product | None] = relationship(back_populates="materials")
    interaction_materials: Mapped[list[InteractionMaterial]] = relationship(back_populates="material")
