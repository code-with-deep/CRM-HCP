"""Healthcare professional ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import HcpStatus
from app.models.mixins import AuditMixin

if TYPE_CHECKING:
    from app.models.interaction import Interaction
    from app.models.interaction_associations import InteractionAttendee


class Hcp(AuditMixin, Base):
    """Healthcare professional targeted by medical representatives."""

    __tablename__ = "hcps"
    __table_args__ = (
        Index("ix_hcps_name_active", "name"),
        Index("ix_hcps_city_state_active", "city", "state"),
        Index("ix_hcps_status_active", "status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(150), nullable=True)
    hospital: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[HcpStatus] = mapped_column(
        Enum(HcpStatus, name="hcp_status", native_enum=False),
        nullable=False,
        default=HcpStatus.ACTIVE,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    interactions: Mapped[list[Interaction]] = relationship(back_populates="hcp")
    attendee_records: Mapped[list[InteractionAttendee]] = relationship(back_populates="hcp")
