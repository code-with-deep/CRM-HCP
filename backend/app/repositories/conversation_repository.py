"""Conversation repositories."""

from uuid import UUID

from sqlalchemy import func, select

from app.models.conversation import ConversationMessage, ConversationSession
from app.models.enums import ConversationSessionStatus
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class ConversationSessionRepository(BaseRepository[ConversationSession]):
    """Data access layer for AI conversation sessions."""

    model = ConversationSession

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        status: ConversationSessionStatus | None = None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[ConversationSession]:
        """List conversation sessions for a user."""
        query = self._base_select(include_deleted=include_deleted).where(
            ConversationSession.user_id == user_id,
        )
        if status:
            query = query.where(ConversationSession.status == status)

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())
        result = await self.session.execute(
            query.order_by(ConversationSession.started_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    """Data access layer for AI conversation messages."""

    model = ConversationMessage

    async def list_by_session(
        self,
        session_id: UUID,
        pagination: PaginationParams,
        *,
        include_deleted: bool = False,
    ) -> PaginatedResponse[ConversationMessage]:
        """List messages for a conversation session in sequence order."""
        query = self._base_select(include_deleted=include_deleted).where(
            ConversationMessage.session_id == session_id,
        )
        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())
        result = await self.session.execute(
            query.order_by(ConversationMessage.sequence_number.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )

    async def list_all_by_session(
        self,
        session_id: UUID,
        *,
        include_deleted: bool = False,
        limit: int = 500,
    ) -> list[ConversationMessage]:
        """Return conversation messages for agent context without pagination constraints."""
        query = (
            self._base_select(include_deleted=include_deleted)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.sequence_number.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_sequence_number(self, session_id: UUID) -> int:
        """Return the next message sequence number for a session."""
        query = select(func.max(ConversationMessage.sequence_number)).where(
            ConversationMessage.session_id == session_id,
            ConversationMessage.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        current_max = result.scalar_one_or_none()
        return 0 if current_max is None else int(current_max) + 1
