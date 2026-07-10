"""Healthcare professional Pydantic schemas."""

from uuid import UUID

from pydantic import EmailStr, Field

from app.models.enums import HcpStatus
from app.schemas.common import AuditSchema, SchemaBase


class HcpBase(SchemaBase):
    """Shared HCP fields."""

    name: str = Field(min_length=1, max_length=255)
    specialization: str | None = Field(default=None, max_length=150)
    hospital: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    status: HcpStatus = HcpStatus.ACTIVE
    notes: str | None = None


class HcpCreate(HcpBase):
    """Schema for creating an HCP."""

    created_by: UUID | None = None


class HcpUpdate(SchemaBase):
    """Schema for updating an HCP."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    specialization: str | None = Field(default=None, max_length=150)
    hospital: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    status: HcpStatus | None = None
    notes: str | None = None
    updated_by: UUID | None = None


class HcpRead(HcpBase, AuditSchema):
    """Internal read schema for HCPs."""


class HcpResponse(HcpRead):
    """API response schema for HCPs."""
