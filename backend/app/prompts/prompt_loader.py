"""Central prompt loader and renderer for the Healthcare CRM AI layer."""

from collections.abc import Callable
from typing import Any

from app.prompts import (
    edit_interaction_prompt,
    followup_prompt,
    intent_prompt,
    log_interaction_prompt,
    materials_prompt,
    planner_prompt,
    response_prompt,
    router_prompt,
    search_hcp_prompt,
    system_prompt,
    validation_prompt,
)

PromptBuilder = Callable[..., str]

# LangGraph node prompt registry
NODE_PROMPT_BUILDERS: dict[str, PromptBuilder] = {
    "system": system_prompt.build,
    "planner": planner_prompt.build,
    "reasoner": intent_prompt.build,
    "router": router_prompt.build,
    "validator": validation_prompt.build,
    "response": response_prompt.build,
}

# Tool prompt registry for LangGraph tool implementations
TOOL_PROMPT_BUILDERS: dict[str, PromptBuilder] = {
    "log_interaction": log_interaction_prompt.build,
    "edit_interaction": edit_interaction_prompt.build,
    "search_hcp": search_hcp_prompt.build,
    "materials_and_samples": materials_prompt.build,
    "outcome_and_followup": followup_prompt.build,
}

PROMPT_ALIASES: dict[str, str] = {
    "intent": "reasoner",
    "followup": "outcome_and_followup",
    "materials": "materials_and_samples",
}


def _resolve_prompt_name(prompt_name: str) -> str:
    """Resolve friendly aliases to canonical prompt names."""
    return PROMPT_ALIASES.get(prompt_name, prompt_name)


def get_node_prompt_builder(prompt_name: str) -> PromptBuilder:
    """Return a LangGraph node prompt builder."""
    resolved_name = _resolve_prompt_name(prompt_name)
    if resolved_name not in NODE_PROMPT_BUILDERS:
        raise KeyError(f"Unknown node prompt: {prompt_name}")
    return NODE_PROMPT_BUILDERS[resolved_name]


def get_tool_prompt_builder(tool_name: str) -> PromptBuilder:
    """Return a LangGraph tool prompt builder."""
    resolved_name = _resolve_prompt_name(tool_name)
    if resolved_name not in TOOL_PROMPT_BUILDERS:
        raise KeyError(f"Unknown tool prompt: {tool_name}")
    return TOOL_PROMPT_BUILDERS[resolved_name]


def load_prompt(prompt_name: str, **kwargs: Any) -> str:
    """Load a prompt by name without rendering contextual variables."""
    if prompt_name == "system":
        return system_prompt.build()
    return render_prompt(prompt_name, **kwargs)


def render_prompt(prompt_name: str, **kwargs: Any) -> str:
    """Render a node prompt with runtime variables."""
    builder = get_node_prompt_builder(prompt_name)
    return builder(**kwargs)


def render_tool_prompt(tool_name: str, **kwargs: Any) -> str:
    """Render a tool prompt with runtime variables."""
    builder = get_tool_prompt_builder(tool_name)
    return builder(**kwargs)


def list_node_prompts() -> list[str]:
    """Return available LangGraph node prompt names."""
    return sorted(NODE_PROMPT_BUILDERS.keys())


def list_tool_prompts() -> list[str]:
    """Return available LangGraph tool prompt names."""
    return sorted(TOOL_PROMPT_BUILDERS.keys())
