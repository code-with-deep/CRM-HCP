"""Unit tests for tool registry."""

from app.langgraph.schemas import ToolName
from app.langgraph.tools.registry import TOOL_REGISTRY, list_registered_tools


def test_all_required_tools_are_registered() -> None:
    """Ensure all five assignment tools are discoverable."""
    registered = set(list_registered_tools())
    assert ToolName.LOG_INTERACTION.value in registered
    assert ToolName.EDIT_INTERACTION.value in registered
    assert ToolName.SEARCH_HCP.value in registered
    assert ToolName.MATERIALS_AND_SAMPLES.value in registered
    assert ToolName.OUTCOME_AND_FOLLOWUP.value in registered
    assert len(TOOL_REGISTRY) == 5
