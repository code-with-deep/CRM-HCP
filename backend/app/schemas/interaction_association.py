"""Interaction association Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.common import AuditSchema, SchemaBase


class InteractionAttendeeBase(SchemaBase):
    """Shared interaction attendee fields."""

    interaction_id: UUID
    attendee_name: str = Field(min_length=1, max_length=255)
    attendee_role: str | None = Field(default=None, max_length=100)
    hcp_id: UUID | None = None


class InteractionAttendeeCreate(InteractionAttendeeBase):
    """Schema for creating an interaction attendee."""

    created_by: UUID | None = None


class InteractionAttendeeUpdate(SchemaBase):
    """Schema for updating an interaction attendee."""

    attendee_name: str | None = Field(default=None, min_length=1, max_length=255)
    attendee_role: str | None = Field(default=None, max_length=100)
    hcp_id: UUID | None = None
    updated_by: UUID | None = None


class InteractionAttendeeRead(InteractionAttendeeBase, AuditSchema):
    """Internal read schema for interaction attendees."""


class InteractionAttendeeResponse(InteractionAttendeeRead):
    """API response schema for interaction attendees."""


class InteractionTopicBase(SchemaBase):
    """Shared interaction topic association fields."""

    interaction_id: UUID
    topic_id: UUID
    discussion_notes: str | None = None


class InteractionTopicCreate(InteractionTopicBase):
    """Schema for creating an interaction topic association."""

    created_by: UUID | None = None


class InteractionTopicUpdate(SchemaBase):
    """Schema for updating an interaction topic association."""

    topic_id: UUID | None = None
    discussion_notes: str | None = None
    updated_by: UUID | None = None


class InteractionTopicRead(InteractionTopicBase, AuditSchema):
    """Internal read schema for interaction topics."""


class InteractionTopicResponse(InteractionTopicRead):
    """API response schema for interaction topics."""


class InteractionMaterialBase(SchemaBase):
    """Shared interaction material association fields."""

    interaction_id: UUID
    material_id: UUID
    quantity_shared: int = Field(default=1, ge=1)
    notes: str | None = None


class InteractionMaterialCreate(InteractionMaterialBase):
    """Schema for creating an interaction material association."""

    created_by: UUID | None = None


class InteractionMaterialUpdate(SchemaBase):
    """Schema for updating an interaction material association."""

    material_id: UUID | None = None
    quantity_shared: int | None = Field(default=None, ge=1)
    notes: str | None = None
    updated_by: UUID | None = None


class InteractionMaterialRead(InteractionMaterialBase, AuditSchema):
    """Internal read schema for interaction materials."""


class InteractionMaterialResponse(InteractionMaterialRead):
    """API response schema for interaction materials."""


class InteractionSampleBase(SchemaBase):
    """Shared interaction sample association fields."""

    interaction_id: UUID
    sample_id: UUID
    quantity_distributed: int = Field(default=1, ge=1)
    notes: str | None = None


class InteractionSampleCreate(InteractionSampleBase):
    """Schema for creating an interaction sample association."""

    created_by: UUID | None = None


class InteractionSampleUpdate(SchemaBase):
    """Schema for updating an interaction sample association."""

    sample_id: UUID | None = None
    quantity_distributed: int | None = Field(default=None, ge=1)
    notes: str | None = None
    updated_by: UUID | None = None


class InteractionSampleRead(InteractionSampleBase, AuditSchema):
    """Internal read schema for interaction samples."""


class InteractionSampleResponse(InteractionSampleRead):
    """API response schema for interaction samples."""


class InteractionProductBase(SchemaBase):
    """Shared interaction product association fields."""

    interaction_id: UUID
    product_id: UUID
    notes: str | None = None


class InteractionProductCreate(InteractionProductBase):
    """Schema for creating an interaction product association."""

    created_by: UUID | None = None


class InteractionProductUpdate(SchemaBase):
    """Schema for updating an interaction product association."""

    product_id: UUID | None = None
    notes: str | None = None
    updated_by: UUID | None = None


class InteractionProductRead(InteractionProductBase, AuditSchema):
    """Internal read schema for interaction products."""


class InteractionProductResponse(InteractionProductRead):
    """API response schema for interaction products."""
