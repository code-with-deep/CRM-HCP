"""Sample repository."""

from uuid import UUID

from sqlalchemy import func, or_, select

from app.models.sample import Sample
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class SampleRepository(BaseRepository[Sample]):
    """Data access layer for drug sample inventory."""

    model = Sample

    async def search(
        self,
        *,
        search_term: str | None,
        product_id: UUID | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[Sample]:
        """Search samples by name, lot number, or product."""
        query = self._base_select(include_deleted=include_deleted)

        if search_term:
            pattern = f"%{search_term.strip()}%"
            query = query.where(
                or_(
                    Sample.name.ilike(pattern),
                    Sample.lot_number.ilike(pattern),
                    Sample.description.ilike(pattern),
                ),
            )

        if product_id:
            query = query.where(Sample.product_id == product_id)

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(Sample.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )

    async def list_available(
        self,
        pagination: PaginationParams,
    ) -> PaginatedResponse[Sample]:
        """List samples with available inventory."""
        query = self._base_select().where(Sample.quantity_available > 0)
        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())
        result = await self.session.execute(
            query.order_by(Sample.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
