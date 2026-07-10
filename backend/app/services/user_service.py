"""User service skeleton."""

from app.repositories.user_repository import UserRepository


class UserService:
    """Application service for CRM user operations."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
