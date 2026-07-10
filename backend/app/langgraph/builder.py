"""LangGraph builder for the Healthcare CRM AI agent."""

from langgraph.graph import END, START, StateGraph

from app.langgraph.nodes import (
    intent_reasoner_node,
    planner_node,
    response_generator_node,
    state_updater_node,
    tool_executor_node,
    tool_router_node,
    validation_node,
)
from app.langgraph.routing import route_after_router, route_after_validation
from app.langgraph.state import AgentState


def build_agent_graph():
    """Build and compile the modular LangGraph agent."""
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("intent_reasoner", intent_reasoner_node)
    graph_builder.add_node("tool_router", tool_router_node)
    graph_builder.add_node("tool_executor", tool_executor_node)
    graph_builder.add_node("validator", validation_node)
    graph_builder.add_node("state_updater", state_updater_node)
    graph_builder.add_node("response_generator", response_generator_node)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "intent_reasoner")
    graph_builder.add_edge("intent_reasoner", "tool_router")
    graph_builder.add_conditional_edges(
        "tool_router",
        route_after_router,
        {
            "tool_executor": "tool_executor",
            "response_generator": "response_generator",
        },
    )
    graph_builder.add_edge("tool_executor", "validator")
    graph_builder.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "intent_reasoner": "intent_reasoner",
            "state_updater": "state_updater",
        },
    )
    graph_builder.add_edge("state_updater", "response_generator")
    graph_builder.add_edge("response_generator", END)

    return graph_builder.compile()


def get_compiled_graph():
    """Return the compiled LangGraph agent."""
    return build_agent_graph()
