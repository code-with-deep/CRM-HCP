"""Shared Pydantic schema primitives."""

from datetime import datetime
from math import ceil
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SchemaT = TypeVar("SchemaT")


class SchemaBase(BaseModel):
    """Base schema with ORM compatibility."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ApplicationInfoResponse(SchemaBase):
    """Root endpoint response schema."""

    name: str = Field(..., description="Application name.")
    version: str = Field(..., description="Application version.")
    status: str = Field(..., description="Current application status.")


class HealthCheckResponse(SchemaBase):
    """Health check endpoint response schema."""

    name: str = Field(..., description="Application name.")
    version: str = Field(..., description="Application version.")
    status: str = Field(..., description="Overall health status.")
    database: str = Field(..., description="Database connectivity status.")


class AuditSchema(SchemaBase):
    """Audit fields returned by read and response schemas."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None


class PaginationParams(SchemaBase):
    """Standard pagination query parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calculate SQL offset from page and page size."""
        return (self.page - 1) * self.page_size


class PaginationMeta(SchemaBase):
    """Pagination metadata for list responses."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(SchemaBase, Generic[SchemaT]):
    """Generic paginated response wrapper."""

    items: list[SchemaT]
    meta: PaginationMeta

    @classmethod
    def create(
        cls,
        *,
        items: list[SchemaT],
        total_items: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[SchemaT]":
        """Build a paginated response from query results."""
        total_pages = ceil(total_items / pagination.page_size) if total_items else 0
        return cls(
            items=items,
            meta=PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=pagination.page < total_pages,
                has_previous=pagination.page > 1 and total_pages > 0,
            ),
        )
