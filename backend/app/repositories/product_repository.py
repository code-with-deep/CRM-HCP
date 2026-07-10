"""Product repository."""

from sqlalchemy import func, or_, select

from app.models.product import Product
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class ProductRepository(BaseRepository[Product]):
    """Data access layer for pharmaceutical products."""

    model = Product

    async def search(
        self,
        *,
        search_term: str | None,
        category: str | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[Product]:
        """Search products by name, brand, or category."""
        query = self._base_select(include_deleted=include_deleted)

        if search_term:
            pattern = f"%{search_term.strip()}%"
            query = query.where(
                or_(
                    Product.product_name.ilike(pattern),
                    Product.brand.ilike(pattern),
                    Product.category.ilike(pattern),
                ),
            )

        if category:
            query = query.where(Product.category.ilike(f"%{category.strip()}%"))

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(Product.product_name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
