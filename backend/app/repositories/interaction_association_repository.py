"""Interaction association repositories."""

from uuid import UUID

from sqlalchemy import Select, func, select

from app.models.interaction_associations import (
    InteractionAttendee,
    InteractionMaterial,
    InteractionProduct,
    InteractionSample,
    InteractionTopic,
)
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


async def paginate_query(
    repository: BaseRepository,
    query: Select,
    pagination: PaginationParams,
) -> PaginatedResponse:
    """Execute a paginated query using repository session."""
    total_result = await repository.session.execute(
        select(func.count()).select_from(query.subquery()),
    )
    total_items = int(total_result.scalar_one())
    result = await repository.session.execute(
        query.offset(pagination.offset).limit(pagination.page_size),
    )
    return PaginatedResponse.create(
        items=list(result.scalars().all()),
        total_items=total_items,
        pagination=pagination,
    )


class InteractionAttendeeRepository(BaseRepository[InteractionAttendee]):
    """Data access layer for interaction attendees."""

    model = InteractionAttendee

    async def list_by_interaction(
        self,
        interaction_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResponse[InteractionAttendee]:
        """List attendees for a specific interaction."""
        query = self._base_select().where(InteractionAttendee.interaction_id == interaction_id)
        return await paginate_query(self, query, pagination)


class InteractionTopicRepository(BaseRepository[InteractionTopic]):
    """Data access layer for interaction-topic associations."""

    model = InteractionTopic

    async def list_by_interaction(
        self,
        interaction_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResponse[InteractionTopic]:
        """List topics linked to a specific interaction."""
        query = self._base_select().where(InteractionTopic.interaction_id == interaction_id)
        return await paginate_query(self, query, pagination)


class InteractionMaterialRepository(BaseRepository[InteractionMaterial]):
    """Data access layer for interaction-material associations."""

    model = InteractionMaterial

    async def list_by_interaction(
        self,
        interaction_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResponse[InteractionMaterial]:
        """List materials shared during a specific interaction."""
        query = self._base_select().where(InteractionMaterial.interaction_id == interaction_id)
        return await paginate_query(self, query, pagination)


class InteractionSampleRepository(BaseRepository[InteractionSample]):
    """Data access layer for interaction-sample associations."""

    model = InteractionSample

    async def list_by_interaction(
        self,
        interaction_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResponse[InteractionSample]:
        """List samples distributed during a specific interaction."""
        query = self._base_select().where(InteractionSample.interaction_id == interaction_id)
        return await paginate_query(self, query, pagination)


class InteractionProductRepository(BaseRepository[InteractionProduct]):
    """Data access layer for interaction-product associations."""

    model = InteractionProduct

    async def list_by_interaction(
        self,
        interaction_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResponse[InteractionProduct]:
        """List products discussed during a specific interaction."""
        query = self._base_select().where(InteractionProduct.interaction_id == interaction_id)
        return await paginate_query(self, query, pagination)
