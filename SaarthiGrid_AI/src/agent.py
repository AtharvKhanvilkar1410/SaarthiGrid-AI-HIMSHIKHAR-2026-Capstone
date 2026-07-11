"""LangGraph assembly for the SaarthiGrid AI agent."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes import (
    eligibility_checker_node,
    guardrail_node,
    logger_node,
    profile_parser_node,
    response_generator_node,
    scheme_matcher_node,
)
from .state import AgentState


def _route_after_guardrail(state: AgentState) -> str:
    """Route execution based on guardrail outcome.

    Args:
        state: AgentState after ``guardrail_node``.

    Returns:
        ``valid`` when the query should continue, otherwise ``invalid``.
    """

    return "valid" if state.get("is_valid_query") else "invalid"


graph = StateGraph(AgentState)
graph.add_node("guardrail_node", guardrail_node)
graph.add_node("profile_parser_node", profile_parser_node)
graph.add_node("scheme_matcher_node", scheme_matcher_node)
graph.add_node("eligibility_checker_node", eligibility_checker_node)
graph.add_node("response_generator_node", response_generator_node)
graph.add_node("logger_node", logger_node)

graph.set_entry_point("guardrail_node")
graph.add_conditional_edges(
    "guardrail_node",
    _route_after_guardrail,
    {
        "valid": "profile_parser_node",
        "invalid": END,
    },
)
graph.add_edge("profile_parser_node", "scheme_matcher_node")
graph.add_edge("scheme_matcher_node", "eligibility_checker_node")
graph.add_edge("eligibility_checker_node", "response_generator_node")
graph.add_edge("response_generator_node", "logger_node")
graph.add_edge("logger_node", END)

app_graph = graph.compile()
