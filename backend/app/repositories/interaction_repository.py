"""Interaction repository."""

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.enums import InteractionStatus
from app.models.interaction import Interaction
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class InteractionRepository(BaseRepository[Interaction]):
    """Data access layer for HCP interactions."""

    model = Interaction

    async def get_with_relations(
        self,
        interaction_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Interaction | None:
        """Retrieve an interaction with eagerly loaded associations."""
        query = (
            self._base_select(include_deleted=include_deleted)
            .where(Interaction.id == interaction_id)
            .options(
                selectinload(Interaction.attendees),
                selectinload(Interaction.topics),
                selectinload(Interaction.materials),
                selectinload(Interaction.samples),
                selectinload(Interaction.products),
                selectinload(Interaction.hcp),
                selectinload(Interaction.interaction_type),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        user_id: UUID | None = None,
        hcp_id: UUID | None = None,
        status: InteractionStatus | None = None,
        interaction_date_from: date | None = None,
        interaction_date_to: date | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[Interaction]:
        """Search interactions using common CRM filters."""
        query = self._base_select(include_deleted=include_deleted)

        if user_id:
            query = query.where(Interaction.user_id == user_id)
        if hcp_id:
            query = query.where(Interaction.hcp_id == hcp_id)
        if status:
            query = query.where(Interaction.status == status)
        if interaction_date_from:
            query = query.where(Interaction.interaction_date >= interaction_date_from)
        if interaction_date_to:
            query = query.where(Interaction.interaction_date <= interaction_date_to)

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(Interaction.interaction_date.desc(), Interaction.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )

    async def get_by_conversation_id(
        self,
        conversation_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Interaction | None:
        """Retrieve an interaction linked to a conversation session."""
        query = self._base_select(include_deleted=include_deleted).where(
            Interaction.conversation_id == conversation_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
