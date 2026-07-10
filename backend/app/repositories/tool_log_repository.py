"""Tool execution log repository."""

from uuid import UUID

from sqlalchemy import func, select

from app.models.enums import ToolExecutionStatus
from app.models.tool_log import ToolExecutionLog
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class ToolExecutionLogRepository(BaseRepository[ToolExecutionLog]):
    """Data access layer for LangGraph tool execution logs."""

    model = ToolExecutionLog

    async def list_by_session(
        self,
        session_id: UUID,
        pagination: PaginationParams,
        *,
        include_deleted: bool = False,
    ) -> PaginatedResponse[ToolExecutionLog]:
        """List tool execution logs for a conversation session."""
        query = self._base_select(include_deleted=include_deleted).where(
            ToolExecutionLog.session_id == session_id,
        )
        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())
        result = await self.session.execute(
            query.order_by(ToolExecutionLog.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )

    async def search(
        self,
        *,
        tool_name: str | None = None,
        status: ToolExecutionStatus | None = None,
        session_id: UUID | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[ToolExecutionLog]:
        """Search tool execution logs for debugging and observability."""
        query = self._base_select(include_deleted=include_deleted)

        if tool_name:
            query = query.where(ToolExecutionLog.tool_name.ilike(f"%{tool_name.strip()}%"))
        if status:
            query = query.where(ToolExecutionLog.status == status)
        if session_id:
            query = query.where(ToolExecutionLog.session_id == session_id)

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())
        result = await self.session.execute(
            query.order_by(ToolExecutionLog.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
