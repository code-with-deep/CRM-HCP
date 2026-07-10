"""Backward-compatible prompt access for LangGraph modules.

Prompt content lives in app.prompts. This module delegates to the shared
prompt loader so LangGraph nodes do not hardcode prompt text.
"""

from app.prompts.prompt_loader import load_prompt, render_prompt, render_tool_prompt

__all__ = ["load_prompt", "render_prompt", "render_tool_prompt"]
