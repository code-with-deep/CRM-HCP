"""Material repository."""

from uuid import UUID

from sqlalchemy import func, or_, select

from app.models.enums import MaterialType
from app.models.material import Material
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class MaterialRepository(BaseRepository[Material]):
    """Data access layer for promotional materials."""

    model = Material

    async def search(
        self,
        *,
        search_term: str | None,
        material_type: MaterialType | None = None,
        product_id: UUID | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[Material]:
        """Search materials by name, type, or related product."""
        query = self._base_select(include_deleted=include_deleted)

        if search_term:
            pattern = f"%{search_term.strip()}%"
            query = query.where(
                or_(Material.name.ilike(pattern), Material.description.ilike(pattern)),
            )

        if material_type:
            query = query.where(Material.material_type == material_type)
        if product_id:
            query = query.where(Material.product_id == product_id)

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(Material.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
