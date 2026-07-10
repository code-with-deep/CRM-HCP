"""SearchHCPTool implementation."""

from typing import Any

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState, HcpContext, get_interaction_draft
from app.langgraph.tools.base_tool import BaseCrmTool
from app.langgraph.tools.dependencies import ToolDependencies
from app.langgraph.tools.schemas import SearchHcpToolInput, ToolExecutionResult
from app.prompts.schemas import HcpSearchOutput

logger = get_logger(__name__)


class SearchHcpTool(BaseCrmTool):
    """Search healthcare professionals and enrich results with CRM history."""

    name = ToolName.SEARCH_HCP
    description = (
        "Search healthcare professionals by name, hospital, city, specialization, or partial "
        "name with typo tolerance and return matching HCP details with recent interactions."
    )
    input_schema = SearchHcpToolInput
    output_schema = HcpSearchOutput
    prompt_name = "search_hcp"

    async def execute(
        self,
        *,
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        """Search PostgreSQL for matching HCP records."""
        try:
            validated_input = self.input_schema.model_validate(tool_input)
            user_instruction = validated_input.user_instruction or self.build_user_instruction(
                state,
                tool_input,
            )

            llm_output = await self.invoke_structured_llm(
                dependencies=dependencies,
                output_schema=HcpSearchOutput,
                prompt_name=self.prompt_name,
                prompt_kwargs={
                    "conversation_history": self.serialize_history(state),
                    "current_hcp": str(state.get("current_hcp") or {}),
                    "user_query": user_instruction,
                },
                user_content=user_instruction,
            )

            search_data = await dependencies.hcp_tool_service.search_with_context(
                llm_output.search_request,
                search_reasoning=llm_output.search_reasoning,
            )

            if not search_data.results:
                return self.success(
                    self.name,
                    "No matching healthcare professionals were found.",
                    metadata={
                        "search_request": llm_output.search_request.model_dump(mode="json"),
                        "search_results": [],
                        "total_results": 0,
                    },
                )

            primary_result = search_data.results[0]
            hcp_context = HcpContext(
                hcp_id=primary_result.hcp_id,
                name=primary_result.name,
                specialization=primary_result.specialization,
                hospital=primary_result.hospital,
                city=primary_result.city,
                state=primary_result.state,
            ).to_serializable()

            interaction_patch = {}
            if primary_result.name and not get_interaction_draft(state).hcp_name:
                interaction_patch["hcp_name"] = primary_result.name

            return self.success(
                self.name,
                f"Found {search_data.total_results} matching healthcare professional(s).",
                interaction_patch=interaction_patch,
                hcp_context=hcp_context,
                metadata={
                    "search_request": llm_output.search_request.model_dump(mode="json"),
                    "search_results": [item.model_dump(mode="json") for item in search_data.results],
                    "total_results": search_data.total_results,
                },
            )
        except RuntimeError as exc:
            logger.error("SearchHcpTool LLM failure: %s", str(exc), exc_info=exc)
            return self.failure(self.name, "I could not process the HCP search request right now.")
        except Exception as exc:
            logger.error("SearchHcpTool failed: %s", str(exc), exc_info=exc)
            return self.failure(self.name, f"Failed to search HCP records: {exc}")


search_hcp_tool = SearchHcpTool()
