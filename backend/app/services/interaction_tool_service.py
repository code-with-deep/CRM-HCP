"""Service layer for interaction-related tool support."""

from app.repositories.interaction_repository import InteractionRepository


class InteractionToolService:
    """Business operations supporting interaction tools."""

    def __init__(self, interaction_repository: InteractionRepository) -> None:
        self._interaction_repository = interaction_repository
