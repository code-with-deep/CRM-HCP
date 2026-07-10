"""Interaction type repository."""

from sqlalchemy import func, select

from app.models.interaction_type import InteractionType
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class InteractionTypeRepository(BaseRepository[InteractionType]):
    """Data access layer for interaction type reference data."""

    model = InteractionType

    async def get_by_name(
        self,
        name: str,
        *,
        include_deleted: bool = False,
    ) -> InteractionType | None:
        """Retrieve an interaction type by name."""
        query = self._base_select(include_deleted=include_deleted).where(
            InteractionType.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        pagination: PaginationParams,
    ) -> PaginatedResponse[InteractionType]:
        """List active interaction types."""
        query = self._base_select().where(InteractionType.is_active.is_(True))
        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())
        result = await self.session.execute(
            query.order_by(InteractionType.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
