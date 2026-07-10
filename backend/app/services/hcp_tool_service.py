"""Service layer for HCP search tool operations."""

from app.langgraph.tools.schemas import HcpSearchResultItem, SearchHcpToolData
from app.prompts.schemas import HcpSearchRequest
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.common import PaginationParams


class HcpToolService:
    """Business operations supporting SearchHCPTool."""

    def __init__(
        self,
        hcp_repository: HcpRepository,
        interaction_repository: InteractionRepository,
    ) -> None:
        self._hcp_repository = hcp_repository
        self._interaction_repository = interaction_repository

    async def search_with_context(
        self,
        search_request: HcpSearchRequest,
        *,
        search_reasoning: str,
    ) -> SearchHcpToolData:
        """Search HCPs and enrich results with interaction history."""
        search_terms = self._build_search_terms(search_request)
        collected_results: dict[str, HcpSearchResultItem] = {}

        for term in search_terms:
            paginated = await self._hcp_repository.search(
                search_term=term,
                city=search_request.city,
                state=search_request.state,
                pagination=PaginationParams(page=1, page_size=10),
            )
            for hcp in paginated.items:
                if str(hcp.id) in collected_results:
                    continue

                interactions = await self._interaction_repository.search(
                    hcp_id=hcp.id,
                    pagination=PaginationParams(page=1, page_size=5),
                )
                interaction_summaries = [
                    {
                        "interaction_id": str(interaction.id),
                        "interaction_date": interaction.interaction_date.isoformat(),
                        "status": interaction.status.value,
                        "summary": interaction.summary,
                        "sentiment": interaction.sentiment.value if interaction.sentiment else None,
                        "follow_up": interaction.follow_up,
                    }
                    for interaction in interactions.items
                ]
                follow_ups = [
                    item["follow_up"]
                    for item in interaction_summaries
                    if item.get("follow_up")
                ]

                collected_results[str(hcp.id)] = HcpSearchResultItem(
                    hcp_id=str(hcp.id),
                    name=hcp.name,
                    specialization=hcp.specialization,
                    hospital=hcp.hospital,
                    city=hcp.city,
                    state=hcp.state,
                    email=hcp.email,
                    phone=hcp.phone,
                    previous_interactions=interaction_summaries,
                    recent_follow_ups=follow_ups,
                )

        results = list(collected_results.values())
        return SearchHcpToolData(
            search_reasoning=search_reasoning,
            results=results,
            total_results=len(results),
        )

    @staticmethod
    def _build_search_terms(search_request: HcpSearchRequest) -> list[str]:
        """Build typo-tolerant search terms from structured search output."""
        terms: list[str] = []

        for candidate in (
            search_request.query_text,
            search_request.doctor_name,
            search_request.hospital,
            search_request.specialization,
            *search_request.alternate_spellings,
        ):
            if candidate and candidate.strip() and candidate.strip() not in terms:
                terms.append(candidate.strip())

        return terms or [""]
