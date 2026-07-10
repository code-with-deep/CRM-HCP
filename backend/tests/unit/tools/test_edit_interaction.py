"""Unit tests for EditInteractionTool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.langgraph.schemas import ToolName
from app.langgraph.state import InteractionDraft, create_initial_state
from app.langgraph.tools.edit_interaction import EditInteractionTool
from app.prompts.schemas import EditInteractionOutput


@pytest.mark.asyncio
async def test_edit_interaction_tool_updates_only_requested_fields() -> None:
    """Example execution: surgical edit preserves unchanged fields."""
    tool = EditInteractionTool()
    state = create_initial_state(
        user_message="Actually the doctor's name was Dr Sharma and sentiment was negative.",
        current_interaction=InteractionDraft(
            hcp_name="Dr Smith",
            interaction_type="Meeting",
            topics_discussed=["Product X"],
            sentiment="positive",
        ),
    )

    mock_llm_output = EditInteractionOutput(
        hcp_name="Dr Sharma",
        interaction_type="Meeting",
        topics_discussed=["Product X"],
        sentiment="negative",
        fields_updated=["hcp_name", "sentiment"],
    )

    dependencies = MagicMock()
    dependencies.llm_service = MagicMock()
    dependencies.llm_service.ainvoke_structured = AsyncMock(return_value=mock_llm_output)

    result = await tool.execute(
        state=state,
        tool_input={"user_instruction": "Change doctor to Dr Sharma and sentiment to negative."},
        dependencies=dependencies,
    )

    assert result.success is True
    assert result.tool_name == ToolName.EDIT_INTERACTION.value
    assert result.interaction_patch["hcp_name"] == "Dr Sharma"
    assert result.interaction_patch["sentiment"] == "negative"
    assert "interaction_type" not in result.interaction_patch
    assert "topics_discussed" not in result.interaction_patch
