"""Unit tests for SearchHCPTool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.langgraph.schemas import ToolName
from app.langgraph.state import create_initial_state
from app.langgraph.tools.schemas import HcpSearchResultItem, SearchHcpToolData
from app.langgraph.tools.search_hcp import SearchHcpTool
from app.prompts.schemas import HcpSearchOutput, HcpSearchRequest


@pytest.mark.asyncio
async def test_search_hcp_tool_returns_repository_results() -> None:
    """Example execution: search HCPs and return enriched metadata."""
    tool = SearchHcpTool()
    state = create_initial_state(user_message="Find Dr Sharma at City Hospital.")

    mock_llm_output = HcpSearchOutput(
        search_request=HcpSearchRequest(
            doctor_name="Dr Sharma",
            hospital="City Hospital",
        ),
        search_reasoning="The user is searching for Dr Sharma at City Hospital.",
    )
    mock_search_data = SearchHcpToolData(
        search_reasoning=mock_llm_output.search_reasoning,
        total_results=1,
        results=[
            HcpSearchResultItem(
                hcp_id="11111111-1111-1111-1111-111111111111",
                name="Dr Sharma",
                hospital="City Hospital",
                specialization="Cardiology",
                previous_interactions=[
                    {
                        "interaction_date": "2026-06-01",
                        "follow_up": "Send clinical study",
                    },
                ],
                recent_follow_ups=["Send clinical study"],
            ),
        ],
    )

    dependencies = MagicMock()
    dependencies.llm_service = MagicMock()
    dependencies.llm_service.ainvoke_structured = AsyncMock(return_value=mock_llm_output)
    dependencies.hcp_tool_service = MagicMock()
    dependencies.hcp_tool_service.search_with_context = AsyncMock(return_value=mock_search_data)

    result = await tool.execute(
        state=state,
        tool_input={"user_instruction": "Find Dr Sharma"},
        dependencies=dependencies,
    )

    assert result.success is True
    assert result.tool_name == ToolName.SEARCH_HCP.value
    assert result.hcp_context is not None
    assert result.hcp_context["name"] == "Dr Sharma"
    assert result.metadata["total_results"] == 1
