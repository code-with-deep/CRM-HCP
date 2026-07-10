"""Healthcare professional repository."""

from uuid import UUID

from sqlalchemy import func, or_, select

from app.models.enums import HcpStatus
from app.models.hcp import Hcp
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class HcpRepository(BaseRepository[Hcp]):
    """Data access layer for healthcare professionals."""

    model = Hcp

    async def search(
        self,
        *,
        search_term: str | None,
        city: str | None = None,
        state: str | None = None,
        status: HcpStatus | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[Hcp]:
        """Search HCPs by name, specialization, hospital, or location."""
        query = self._base_select(include_deleted=include_deleted)

        if search_term:
            pattern = f"%{search_term.strip()}%"
            query = query.where(
                or_(
                    Hcp.name.ilike(pattern),
                    Hcp.specialization.ilike(pattern),
                    Hcp.hospital.ilike(pattern),
                    Hcp.email.ilike(pattern),
                ),
            )

        if city:
            query = query.where(Hcp.city.ilike(f"%{city.strip()}%"))
        if state:
            query = query.where(Hcp.state.ilike(f"%{state.strip()}%"))
        if status:
            query = query.where(Hcp.status == status)

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(Hcp.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )

    async def list_by_ids(self, hcp_ids: list[UUID]) -> list[Hcp]:
        """Retrieve multiple HCPs by identifier."""
        if not hcp_ids:
            return []

        query = self._base_select().where(Hcp.id.in_(hcp_ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())
