"""Product Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.common import AuditSchema, SchemaBase


class ProductBase(SchemaBase):
    """Shared product fields."""

    product_name: str = Field(min_length=1, max_length=150)
    brand: str | None = Field(default=None, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    created_by: UUID | None = None


class ProductUpdate(SchemaBase):
    """Schema for updating a product."""

    product_name: str | None = Field(default=None, min_length=1, max_length=150)
    brand: str | None = Field(default=None, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    updated_by: UUID | None = None


class ProductRead(ProductBase, AuditSchema):
    """Internal read schema for products."""


class ProductResponse(ProductRead):
    """API response schema for products."""
