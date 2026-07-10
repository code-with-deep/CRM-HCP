"""Healthcare professional query service."""

from uuid import UUID

from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.hcp_api import HcpHistoryItem, HcpHistoryResponse, HcpSearchQuery, HcpSearchResultItem

logger = get_logger(__name__)


class HcpService:
    """Application service for healthcare professional search and history."""

    def __init__(
        self,
        *,
        hcp_repository: HcpRepository,
        interaction_repository: InteractionRepository,
    ) -> None:
        self._hcp_repository = hcp_repository
        self._interaction_repository = interaction_repository

    async def search_hcps(self, query: HcpSearchQuery) -> PaginatedResponse[HcpSearchResultItem]:
        """Search HCPs using doctor name, hospital, city, and specialization filters."""
        search_terms = [
            term.strip()
            for term in (query.doctor_name, query.hospital, query.specialization)
            if term and term.strip()
        ]
        search_term = " ".join(search_terms) if search_terms else None

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        paginated = await self._hcp_repository.search(
            search_term=search_term,
            city=query.city,
            pagination=pagination,
        )

        enriched_items: list[HcpSearchResultItem] = []
        for hcp in paginated.items:
            interactions = await self._interaction_repository.search(
                hcp_id=hcp.id,
                pagination=PaginationParams(page=1, page_size=1),
            )
            item = HcpSearchResultItem.model_validate(hcp)
            item.previous_interaction_count = interactions.meta.total_items
            enriched_items.append(item)

        logger.info(
            "HCP search completed term=%s city=%s results=%s",
            search_term,
            query.city,
            len(enriched_items),
        )

        return PaginatedResponse(
            items=enriched_items,
            meta=paginated.meta,
        )

    async def get_hcp_history(self, hcp_id: UUID) -> HcpHistoryResponse:
        """Return previous interactions for an HCP."""
        hcp = await self._hcp_repository.get_by_id(hcp_id)
        if hcp is None:
            raise NotFoundException(
                message="HCP not found",
                detail=f"No HCP exists for id={hcp_id}",
            )

        interactions = await self._interaction_repository.search(
            hcp_id=hcp_id,
            pagination=PaginationParams(page=1, page_size=100),
        )

        history_items = [
            HcpHistoryItem(
                interaction_id=interaction.id,
                interaction_date=interaction.interaction_date.isoformat(),
                status=interaction.status.value,
                summary=interaction.summary,
                sentiment=interaction.sentiment.value if interaction.sentiment else None,
                outcome=interaction.outcome,
                follow_up=interaction.follow_up,
            )
            for interaction in interactions.items
        ]

        logger.info("Retrieved %s interactions for hcp_id=%s", len(history_items), hcp_id)

        return HcpHistoryResponse(
            hcp_id=hcp.id,
            hcp_name=hcp.name,
            interactions=history_items,
        )
