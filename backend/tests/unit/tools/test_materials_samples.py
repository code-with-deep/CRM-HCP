"""Unit tests for MaterialsAndSamplesTool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.langgraph.schemas import ToolName
from app.langgraph.state import create_initial_state
from app.langgraph.tools.materials_samples import MaterialsAndSamplesTool
from app.prompts.schemas import MaterialUpdateSchema


@pytest.mark.asyncio
async def test_materials_and_samples_tool_updates_draft() -> None:
    """Example execution: update materials and samples."""
    tool = MaterialsAndSamplesTool()
    state = create_initial_state(user_message="I shared brochures and left two sample packs.")

    mock_llm_output = MaterialUpdateSchema(
        materials_shared=["Brochure"],
        samples_distributed=["Sample Pack"],
        sample_quantities={"Sample Pack": 2},
        notes="Shared promotional brochure and two sample packs.",
    )

    dependencies = MagicMock()
    dependencies.llm_service = MagicMock()
    dependencies.llm_service.ainvoke_structured = AsyncMock(return_value=mock_llm_output)

    result = await tool.execute(
        state=state,
        tool_input={"user_instruction": "Shared brochures and sample packs."},
        dependencies=dependencies,
    )

    assert result.success is True
    assert result.tool_name == ToolName.MATERIALS_AND_SAMPLES.value
    assert "Brochure" in result.interaction_patch["materials_shared"]
    assert any("Sample Pack" in item for item in result.interaction_patch["samples_distributed"])
