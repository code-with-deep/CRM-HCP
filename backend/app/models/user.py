"""User ORM model for medical representatives and administrators."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import UserRole
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.conversation import ConversationSession
    from app.models.interaction import Interaction


class User(AuditMixin, Base):
    """Medical representative or CRM administrator."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email_active", "email", unique=True),
        Index("ix_users_role_active", "role"),
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.MEDICAL_REPRESENTATIVE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    interactions: Mapped[list[Interaction]] = relationship(
        back_populates="user",
        foreign_keys="Interaction.user_id",
    )
    conversation_sessions: Mapped[list[ConversationSession]] = relationship(
        back_populates="user",
        foreign_keys="ConversationSession.user_id",
    )

    @property
    def full_name(self) -> str:
        """Return the user's display name."""
        return f"{self.first_name} {self.last_name}".strip()
