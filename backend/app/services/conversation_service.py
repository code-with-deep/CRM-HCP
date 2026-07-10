"""Conversation service skeleton."""

from app.repositories.conversation_repository import (
    ConversationMessageRepository,
    ConversationSessionRepository,
)


class ConversationService:
    """Application service for AI conversation session operations."""

    def __init__(
        self,
        session_repository: ConversationSessionRepository,
        message_repository: ConversationMessageRepository,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
