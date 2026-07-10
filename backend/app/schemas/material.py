"""Material Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.models.enums import MaterialType
from app.schemas.common import AuditSchema, SchemaBase


class MaterialBase(SchemaBase):
    """Shared material fields."""

    name: str = Field(min_length=1, max_length=150)
    material_type: MaterialType
    description: str | None = None
    product_id: UUID | None = None


class MaterialCreate(MaterialBase):
    """Schema for creating a material."""

    created_by: UUID | None = None


class MaterialUpdate(SchemaBase):
    """Schema for updating a material."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    material_type: MaterialType | None = None
    description: str | None = None
    product_id: UUID | None = None
    updated_by: UUID | None = None


class MaterialRead(MaterialBase, AuditSchema):
    """Internal read schema for materials."""


class MaterialResponse(MaterialRead):
    """API response schema for materials."""
