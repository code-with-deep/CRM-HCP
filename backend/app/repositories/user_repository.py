"""User repository."""

from sqlalchemy import func, or_, select

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, PaginationParams


class UserRepository(BaseRepository[User]):
    """Data access layer for CRM users."""

    model = User

    async def get_by_email(self, email: str, *, include_deleted: bool = False) -> User | None:
        """Retrieve a user by email address."""
        query = self._base_select(include_deleted=include_deleted).where(
            User.email == email.lower(),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        search_term: str | None,
        pagination: PaginationParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[User]:
        """Search users by name or email."""
        query = self._base_select(include_deleted=include_deleted)

        if search_term:
            pattern = f"%{search_term.strip()}%"
            query = query.where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                ),
            )

        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total_items = int(total_result.scalar_one())

        result = await self.session.execute(
            query.order_by(User.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size),
        )
        return PaginatedResponse.create(
            items=list(result.scalars().all()),
            total_items=total_items,
            pagination=pagination,
        )
