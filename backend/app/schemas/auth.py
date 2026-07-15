"""Pydantic schemas for authentication endpoints."""

from pydantic import EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import SchemaBase


class RegisterRequest(SchemaBase):
    """Request body for user registration."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.MEDICAL_REPRESENTATIVE


class LoginRequest(SchemaBase):
    """Request body for user login."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(SchemaBase):
    """JWT token response returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    full_name: str
