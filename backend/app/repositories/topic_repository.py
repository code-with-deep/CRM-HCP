"""Topic repository."""

from sqlalchemy import func, or_, select

from app.models.topic import Topic
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class TopicRepository(BaseRepository[Topic]):
    """Data access layer for discussion topics."""

    model = Topic

    async def get_by_name(self, name: str, *, include_deleted: bool = False) -> Topic | None:
        """Retrieve a topic by exact name."""
        query = self._base_select(include_deleted=include_deleted).where(Topic.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        search_term: str | None,
        category: str | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[Topic]:
        """Search topics by name, category, or description."""
        query = self._base_select(include_deleted=include_deleted)

        if search_term:
            pattern = f"%{search_term.strip()}%"
            query = query.where(
                or_(
                    Topic.name.ilike(pattern),
                    Topic.category.ilike(pattern),
                    Topic.description.ilike(pattern),
                ),
            )

        if category:
            query = query.where(Topic.category.ilike(f"%{category.strip()}%"))

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(Topic.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
