"""Unit tests for LogInteractionTool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.langgraph.schemas import ToolName
from app.langgraph.state import create_initial_state
from app.langgraph.tools.log_interaction import LogInteractionTool
from app.prompts.schemas import LogInteractionOutput


@pytest.mark.asyncio
async def test_log_interaction_tool_extracts_structured_patch() -> None:
    """Example execution: populate interaction draft from natural language."""
    tool = LogInteractionTool()
    state = create_initial_state(user_message="I met Dr Smith for a lunch meeting today.")

    mock_llm_output = LogInteractionOutput(
        hcp_name="Dr Smith",
        interaction_type="Face to Face",
        interaction_date="2026-07-09",
        topics_discussed=["Product X efficacy"],
        sentiment="positive",
        professional_summary="Discussed Product X efficacy with Dr Smith.",
        fields_populated=["hcp_name", "interaction_type", "interaction_date", "topics_discussed", "sentiment"],
    )

    dependencies = MagicMock()
    dependencies.llm_service = MagicMock()
    dependencies.llm_service.ainvoke_structured = AsyncMock(return_value=mock_llm_output)

    result = await tool.execute(
        state=state,
        tool_input={"user_instruction": state["messages"][0].content},
        dependencies=dependencies,
    )

    assert result.success is True
    assert result.tool_name == ToolName.LOG_INTERACTION.value
    assert result.interaction_patch["hcp_name"] == "Dr Smith"
    assert result.interaction_patch["sentiment"] == "positive"
    assert "Product X efficacy" in result.interaction_patch["topics_discussed"]


@pytest.mark.asyncio
async def test_log_interaction_tool_input_schema_validation() -> None:
    """Validate tool input schema."""
    tool = LogInteractionTool()
    validated = tool.input_schema.model_validate({"user_instruction": "Met Dr Smith"})
    assert validated.user_instruction == "Met Dr Smith"
