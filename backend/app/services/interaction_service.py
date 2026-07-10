"""Interaction persistence service."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.langgraph.state import HcpContext, InteractionDraft
from app.models.enums import InteractionStatus, Sentiment
from app.models.interaction import Interaction
from app.models.interaction_associations import (
    InteractionAttendee,
    InteractionMaterial,
    InteractionProduct,
    InteractionSample,
    InteractionTopic,
)
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_association_repository import (
    InteractionAttendeeRepository,
    InteractionMaterialRepository,
    InteractionProductRepository,
    InteractionSampleRepository,
    InteractionTopicRepository,
)
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.interaction_type_repository import InteractionTypeRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sample_repository import SampleRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.common import PaginationParams
from app.schemas.interaction_api import SaveInteractionRequest
from app.schemas.interaction_detail import InteractionDetailResponse

logger = get_logger(__name__)


class InteractionService:
    """Application service for HCP interaction persistence operations."""

    def __init__(
        self,
        *,
        interaction_repository: InteractionRepository,
        attendee_repository: InteractionAttendeeRepository,
        topic_repository: InteractionTopicRepository,
        material_repository: InteractionMaterialRepository,
        sample_repository: InteractionSampleRepository,
        product_repository: InteractionProductRepository,
        interaction_type_repository: InteractionTypeRepository,
        hcp_repository: HcpRepository,
        topic_catalog_repository: TopicRepository,
        material_catalog_repository: MaterialRepository,
        sample_catalog_repository: SampleRepository,
        product_catalog_repository: ProductRepository,
        session: AsyncSession,
    ) -> None:
        self._interaction_repository = interaction_repository
        self._attendee_repository = attendee_repository
        self._topic_repository = topic_repository
        self._material_repository = material_repository
        self._sample_repository = sample_repository
        self._product_repository = product_repository
        self._interaction_type_repository = interaction_type_repository
        self._hcp_repository = hcp_repository
        self._topic_catalog_repository = topic_catalog_repository
        self._material_catalog_repository = material_catalog_repository
        self._sample_catalog_repository = sample_catalog_repository
        self._product_catalog_repository = product_catalog_repository
        self._session = session

    async def save_interaction(self, request: SaveInteractionRequest) -> InteractionDetailResponse:
        """Persist an AI interaction draft and all related associations."""
        draft = InteractionDraft.from_serializable(request.interaction_draft)
        self._validate_draft(draft)

        hcp_id = await self._resolve_hcp_id(draft, explicit_hcp_id=request.hcp_id)
        interaction_type_id = await self._resolve_interaction_type_id(draft)
        interaction_date = self._parse_date(draft.interaction_date)
        interaction_time = self._parse_time(draft.interaction_time)

        interaction = Interaction(
            hcp_id=hcp_id,
            user_id=request.user_id,
            interaction_type_id=interaction_type_id,
            conversation_id=request.conversation_id,
            interaction_date=interaction_date,
            interaction_time=interaction_time,
            summary=self._build_summary(draft),
            sentiment=self._parse_sentiment(draft.sentiment),
            outcome=draft.outcomes,
            follow_up=draft.follow_up_actions,
            additional_notes=draft.additional_notes,
            ai_generated_summary=request.ai_generated_summary,
            status=request.status,
            created_by=request.user_id,
        )

        try:
            interaction = await self._interaction_repository.create(interaction)
            await self._create_attendees(interaction.id, draft.attendees, created_by=request.user_id)
            await self._create_topics(interaction.id, draft.topics_discussed, created_by=request.user_id)
            await self._create_materials(
                interaction.id,
                draft.materials_shared,
                created_by=request.user_id,
            )
            await self._create_samples(
                interaction.id,
                draft.samples_distributed,
                created_by=request.user_id,
            )
            await self._create_products_from_topics(
                interaction.id,
                draft.topics_discussed,
                created_by=request.user_id,
            )
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            logger.error("Database error saving interaction: %s", str(exc), exc_info=exc)
            raise DatabaseException(detail=str(exc)) from exc

        logger.info("Saved interaction id=%s for hcp_id=%s", interaction.id, hcp_id)
        saved = await self._interaction_repository.get_with_relations(interaction.id)
        if saved is None:
            raise DatabaseException(detail="Interaction was saved but could not be retrieved.")
        return InteractionDetailResponse.model_validate(saved)

    async def get_interaction(self, interaction_id: UUID) -> InteractionDetailResponse:
        """Retrieve a complete interaction with associations."""
        interaction = await self._interaction_repository.get_with_relations(interaction_id)
        if interaction is None:
            raise NotFoundException(
                message="Interaction not found",
                detail=f"No interaction exists for id={interaction_id}",
            )
        return InteractionDetailResponse.model_validate(interaction)

    async def _resolve_hcp_id(
        self,
        draft: InteractionDraft,
        *,
        explicit_hcp_id: UUID | None,
    ) -> UUID:
        """Resolve HCP identifier from explicit value or draft name."""
        if explicit_hcp_id:
            hcp = await self._hcp_repository.get_by_id(explicit_hcp_id)
            if hcp is None:
                raise NotFoundException(
                    message="HCP not found",
                    detail=f"No HCP exists for id={explicit_hcp_id}",
                )
            return explicit_hcp_id

        if not draft.hcp_name:
            raise ValidationException(
                message="HCP is required",
                detail="Provide hcp_id or interaction_draft.hcp_name before saving.",
            )

        search_result = await self._hcp_repository.search(
            search_term=draft.hcp_name,
            pagination=PaginationParams(page=1, page_size=5),
        )
        if not search_result.items:
            raise NotFoundException(
                message="HCP not found",
                detail=f"No HCP matched name '{draft.hcp_name}'.",
            )

        exact_matches = [
            hcp for hcp in search_result.items if hcp.name.lower() == draft.hcp_name.lower()
        ]
        selected = exact_matches[0] if exact_matches else search_result.items[0]
        return selected.id

    async def _resolve_interaction_type_id(self, draft: InteractionDraft) -> UUID:
        """Resolve interaction type from draft or default to Meeting."""
        type_name = draft.interaction_type or "Meeting"
        interaction_type = await self._interaction_type_repository.get_by_name(type_name)
        if interaction_type is None:
            raise ValidationException(
                message="Interaction type not found",
                detail=f"No interaction type exists for name '{type_name}'.",
            )
        return interaction_type.id

    async def _create_attendees(
        self,
        interaction_id: UUID,
        attendees: list[str],
        *,
        created_by: UUID,
    ) -> None:
        """Create attendee records for the interaction."""
        for attendee_name in attendees:
            if not attendee_name.strip():
                continue
            await self._attendee_repository.create(
                InteractionAttendee(
                    interaction_id=interaction_id,
                    attendee_name=attendee_name.strip(),
                    created_by=created_by,
                ),
            )

    async def _create_topics(
        self,
        interaction_id: UUID,
        topics: list[str],
        *,
        created_by: UUID,
    ) -> None:
        """Link topics discussed during the interaction."""
        for topic_name in topics:
            if not topic_name.strip():
                continue
            topic = await self._topic_catalog_repository.get_by_name(topic_name.strip())
            if topic is None:
                continue
            await self._topic_repository.create(
                InteractionTopic(
                    interaction_id=interaction_id,
                    topic_id=topic.id,
                    discussion_notes=topic_name.strip(),
                    created_by=created_by,
                ),
            )

    async def _create_materials(
        self,
        interaction_id: UUID,
        materials: list[str],
        *,
        created_by: UUID,
    ) -> None:
        """Link materials shared during the interaction."""
        for material_name in materials:
            if not material_name.strip():
                continue
            search = await self._material_catalog_repository.search(
                search_term=material_name.strip(),
                pagination=PaginationParams(page=1, page_size=1),
            )
            if not search.items:
                continue
            await self._material_repository.create(
                InteractionMaterial(
                    interaction_id=interaction_id,
                    material_id=search.items[0].id,
                    quantity_shared=1,
                    notes=material_name.strip(),
                    created_by=created_by,
                ),
            )

    async def _create_samples(
        self,
        interaction_id: UUID,
        samples: list[str],
        *,
        created_by: UUID,
    ) -> None:
        """Link samples distributed during the interaction."""
        for sample_name in samples:
            if not sample_name.strip():
                continue
            search = await self._sample_catalog_repository.search(
                search_term=sample_name.strip(),
                pagination=PaginationParams(page=1, page_size=1),
            )
            if not search.items:
                continue
            await self._sample_repository.create(
                InteractionSample(
                    interaction_id=interaction_id,
                    sample_id=search.items[0].id,
                    quantity_distributed=1,
                    notes=sample_name.strip(),
                    created_by=created_by,
                ),
            )

    async def _create_products_from_topics(
        self,
        interaction_id: UUID,
        topics: list[str],
        *,
        created_by: UUID,
    ) -> None:
        """Link products inferred from discussed topics."""
        linked_product_ids: set[UUID] = set()
        for topic_name in topics:
            if not topic_name.strip():
                continue
            search = await self._product_catalog_repository.search(
                search_term=topic_name.strip(),
                pagination=PaginationParams(page=1, page_size=1),
            )
            if not search.items:
                continue
            product_id = search.items[0].id
            if product_id in linked_product_ids:
                continue
            linked_product_ids.add(product_id)
            await self._product_repository.create(
                InteractionProduct(
                    interaction_id=interaction_id,
                    product_id=product_id,
                    notes=topic_name.strip(),
                    created_by=created_by,
                ),
            )

    @staticmethod
    def _validate_draft(draft: InteractionDraft) -> None:
        """Validate minimum required draft fields before persistence."""
        if not draft.interaction_date:
            raise ValidationException(
                message="Interaction date is required",
                detail="interaction_draft.interaction_date must be provided before saving.",
            )

    @staticmethod
    def _parse_date(value: str | None) -> date:
        """Parse ISO date string from interaction draft."""
        if not value:
            raise ValidationException(message="Interaction date is required")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValidationException(
                message="Invalid interaction date",
                detail=f"Could not parse interaction_date '{value}'.",
            ) from exc

    @staticmethod
    def _parse_time(value: str | None) -> time | None:
        """Parse optional time string from interaction draft."""
        if not value:
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        raise ValidationException(
            message="Invalid interaction time",
            detail=f"Could not parse interaction_time '{value}'.",
        )

    @staticmethod
    def _parse_sentiment(value: str | None) -> Sentiment | None:
        """Map draft sentiment string to enum."""
        if not value:
            return None
        try:
            return Sentiment(value.lower())
        except ValueError:
            return None

    @staticmethod
    def _build_summary(draft: InteractionDraft) -> str | None:
        """Build interaction summary from draft fields."""
        parts = [part for part in (draft.outcomes, draft.additional_notes) if part]
        return " | ".join(parts) if parts else None
