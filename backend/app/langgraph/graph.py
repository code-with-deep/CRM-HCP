"""Compiled LangGraph agent export."""

from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from app.langgraph.builder import get_compiled_graph as _compile_graph


@lru_cache
def get_agent_graph() -> CompiledStateGraph:
    """Return a cached compiled Healthcare CRM agent graph."""
    return _compile_graph()
