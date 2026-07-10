"""Sample Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.common import AuditSchema, SchemaBase


class SampleBase(SchemaBase):
    """Shared sample fields."""

    name: str = Field(min_length=1, max_length=150)
    lot_number: str | None = Field(default=None, max_length=100)
    quantity_available: int = Field(default=0, ge=0)
    unit_of_measure: str = Field(default="unit", max_length=50)
    description: str | None = None
    product_id: UUID


class SampleCreate(SampleBase):
    """Schema for creating a sample."""

    created_by: UUID | None = None


class SampleUpdate(SchemaBase):
    """Schema for updating a sample."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    lot_number: str | None = Field(default=None, max_length=100)
    quantity_available: int | None = Field(default=None, ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=50)
    description: str | None = None
    product_id: UUID | None = None
    updated_by: UUID | None = None


class SampleRead(SampleBase, AuditSchema):
    """Internal read schema for samples."""


class SampleResponse(SampleRead):
    """API response schema for samples."""
