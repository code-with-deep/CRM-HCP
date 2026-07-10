"""User Pydantic schemas."""

from uuid import UUID

from pydantic import EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import AuditSchema, SchemaBase


class UserBase(SchemaBase):
    """Shared user fields."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.MEDICAL_REPRESENTATIVE
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""

    password_hash: str = Field(min_length=8, max_length=255)


class UserUpdate(SchemaBase):
    """Schema for updating a user."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password_hash: str | None = Field(default=None, min_length=8, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    updated_by: UUID | None = None


class UserRead(UserBase, AuditSchema):
    """Internal read schema for users."""


class UserResponse(UserRead):
    """API response schema for users."""

    full_name: str
