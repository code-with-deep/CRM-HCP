"""Unit tests for OutcomeAndFollowupTool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.langgraph.schemas import ToolName
from app.langgraph.state import create_initial_state
from app.langgraph.tools.outcome_followup import OutcomeAndFollowupTool
from app.prompts.schemas import FollowUpUpdateSchema


@pytest.mark.asyncio
async def test_outcome_and_followup_tool_updates_draft() -> None:
    """Example execution: update outcomes and follow-up actions."""
    tool = OutcomeAndFollowupTool()
    state = create_initial_state(
        user_message="We agreed to revisit efficacy data next Friday.",
    )

    mock_llm_output = FollowUpUpdateSchema(
        outcomes="Agreed to review efficacy data.",
        follow_up_actions="Schedule follow-up meeting.",
        follow_up_date="2026-07-16",
        reminder="Prepare updated efficacy deck.",
        suggested_follow_up_summary="Follow up next Friday with updated efficacy data.",
    )

    dependencies = MagicMock()
    dependencies.llm_service = MagicMock()
    dependencies.llm_service.ainvoke_structured = AsyncMock(return_value=mock_llm_output)

    result = await tool.execute(
        state=state,
        tool_input={"user_instruction": "Follow up next Friday."},
        dependencies=dependencies,
    )

    assert result.success is True
    assert result.tool_name == ToolName.OUTCOME_AND_FOLLOWUP.value
    assert result.interaction_patch["outcomes"] == "Agreed to review efficacy data."
    assert "Follow-up date: 2026-07-16" in result.interaction_patch["follow_up_actions"]
