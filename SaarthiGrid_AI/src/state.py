"""Shared LangGraph state definition for SaarthiGrid AI."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State passed between all nodes in the SaarthiGrid LangGraph pipeline."""

    farmer_profile: dict[str, Any]
    raw_query: str
    is_valid_query: bool
    guardrail_message: str
    structured_query: str
    matched_schemes: list[dict[str, Any]]
    eligibility_results: list[dict[str, Any]]
    final_response: str
    agent_log: list[dict[str, Any]]
    error: str
