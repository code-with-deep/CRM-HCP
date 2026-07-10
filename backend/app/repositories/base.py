"""Generic repository primitives and shared query helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse, PaginationParams

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Reusable async repository with soft-delete aware CRUD operations."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """Return the active async database session."""
        return self._session

    def _active_records_filter(self, query: Select[Any]) -> Select[Any]:
        """Exclude soft-deleted records from a query."""
        return query.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]

    def _base_select(self, include_deleted: bool = False) -> Select[Any]:
        """Create a base select statement for the repository model."""
        query = select(self.model)
        if not include_deleted:
            query = self._active_records_filter(query)
        return query

    async def create(self, entity: ModelT) -> ModelT:
        """Persist a new entity."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ModelT | None:
        """Retrieve an entity by primary key."""
        query = self._base_select(include_deleted=include_deleted).where(
            self.model.id == entity_id,  # type: ignore[attr-defined]
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        pagination: PaginationParams,
        *,
        include_deleted: bool = False,
    ) -> PaginatedResponse[ModelT]:
        """Return a paginated list of entities."""
        base_query = self._base_select(include_deleted=include_deleted)
        total_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self._session.execute(total_query)
        total_items = int(total_result.scalar_one())

        query = (
            base_query.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self._session.execute(query)
        items = list(result.scalars().all())
        return PaginatedResponse.create(
            items=items,
            total_items=total_items,
            pagination=pagination,
        )

    async def update(self, entity: ModelT) -> ModelT:
        """Flush updates for a tracked entity."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def soft_delete(
        self,
        entity: ModelT,
        *,
        deleted_by: UUID | None = None,
    ) -> ModelT:
        """Soft delete an entity by setting deleted_at."""
        entity.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
        entity.updated_by = deleted_by  # type: ignore[attr-defined]
        return await self.update(entity)

    async def delete(
        self,
        entity: ModelT,
        *,
        deleted_by: UUID | None = None,
        hard_delete: bool = False,
    ) -> None:
        """Delete an entity using soft delete by default."""
        if hard_delete:
            await self._session.delete(entity)
            await self._session.flush()
            return

        await self.soft_delete(entity, deleted_by=deleted_by)
