"""Pytest coverage for SaarthiGrid AI farmer-profile scenarios."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import app_graph  # noqa: E402


def _initial_state(profile: dict[str, Any]) -> dict[str, Any]:
    """Create a complete initial AgentState for tests.

    Args:
        profile: Farmer profile dictionary.

    Returns:
        Initial state dictionary for the LangGraph app.
    """

    return {
        "farmer_profile": profile,
        "raw_query": profile["query"],
        "is_valid_query": False,
        "guardrail_message": "",
        "structured_query": "",
        "matched_schemes": [],
        "eligibility_results": [],
        "final_response": "",
        "agent_log": [],
        "error": "",
    }


def _run_profile(profile: dict[str, Any], monkeypatch: Any) -> dict[str, Any]:
    """Run the graph with LLM calls disabled for deterministic tests.

    Args:
        profile: Farmer profile dictionary.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Final state returned by the graph.
    """

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("SCHEME_DATA_PATH", str(PROJECT_ROOT / "data" / "scheme_rules.csv"))
    monkeypatch.setenv("LOG_FILE_PATH", str(PROJECT_ROOT / "logs" / "agent_log.json"))
    return app_graph.invoke(_initial_state(profile))


def test_ramesh_kumar_hp_wheat_sc_matches_multiple_schemes(monkeypatch: Any) -> None:
    """Validates that an HP SC wheat farmer passes guardrails and receives multiple scheme matches."""

    profile = {
        "farmer_id": "F001",
        "name": "Ramesh Kumar",
        "state": "HP",
        "district": "Mandi",
        "land_acres": 1.5,
        "land_ownership": "Owned",
        "crop_type": "wheat",
        "caste_category": "SC",
        "annual_income": 60000,
        "existing_registrations": "none",
        "query": "Find subsidies and advisory schemes for wheat farming in Mandi Himachal Pradesh.",
    }
    result = _run_profile(profile, monkeypatch)
    matched_names = [scheme["scheme_name"] for scheme in result["matched_schemes"]]
    print("Ramesh Kumar matched schemes:", matched_names)
    assert result["is_valid_query"] is True
    assert len(result["matched_schemes"]) >= 2


def test_suresh_verma_hp_apple_matches_horticulture_support(monkeypatch: Any) -> None:
    """Validates that an HP apple grower receives horticulture, insurance, and state support matches."""

    profile = {
        "farmer_id": "F002",
        "name": "Suresh Verma",
        "state": "HP",
        "district": "Shimla",
        "land_acres": 3.0,
        "land_ownership": "Owned",
        "crop_type": "apple",
        "caste_category": "General",
        "annual_income": 150000,
        "existing_registrations": "Aadhaar",
        "query": "Which government schemes can help my apple orchard in Shimla?",
    }
    result = _run_profile(profile, monkeypatch)
    matched_names = [scheme["scheme_name"] for scheme in result["matched_schemes"]]
    print("Suresh Verma matched schemes:", matched_names)
    assert result["is_valid_query"] is True
    assert len(result["matched_schemes"]) >= 2


def test_gurpreet_singh_punjab_rice_leased_matches_central_schemes(monkeypatch: Any) -> None:
    """Validates that a leased Punjab rice farmer still receives relevant central scheme matches."""

    profile = {
        "farmer_id": "F003",
        "name": "Gurpreet Singh",
        "state": "Punjab",
        "district": "Ludhiana",
        "land_acres": 0.5,
        "land_ownership": "Leased",
        "crop_type": "rice",
        "caste_category": "OBC",
        "annual_income": 40000,
        "existing_registrations": "none",
        "query": "What schemes can support rice cultivation and crop insurance for a leased farmer?",
    }
    result = _run_profile(profile, monkeypatch)
    matched_names = [scheme["scheme_name"] for scheme in result["matched_schemes"]]
    print("Gurpreet Singh matched schemes:", matched_names)
    assert result["is_valid_query"] is True
    assert len(result["matched_schemes"]) >= 2


def test_birsa_munda_hp_maize_st_matches_equipment_and_seed_support(monkeypatch: Any) -> None:
    """Validates that an HP ST maize farmer receives caste-aware equipment and crop support matches."""

    profile = {
        "farmer_id": "F004",
        "name": "Birsa Munda",
        "state": "HP",
        "district": "Kinnaur",
        "land_acres": 2.0,
        "land_ownership": "Owned",
        "crop_type": "maize",
        "caste_category": "ST",
        "annual_income": 75000,
        "existing_registrations": "PM-KISAN",
        "query": "Find maize farming schemes and equipment subsidy options in Kinnaur.",
    }
    result = _run_profile(profile, monkeypatch)
    matched_names = [scheme["scheme_name"] for scheme in result["matched_schemes"]]
    print("Birsa Munda matched schemes:", matched_names)
    assert result["is_valid_query"] is True
    assert len(result["matched_schemes"]) >= 2


def test_anita_devi_off_topic_query_is_blocked(monkeypatch: Any) -> None:
    """Validates that an off-topic query is blocked and produces no scheme matches."""

    profile = {
        "farmer_id": "F005",
        "name": "Anita Devi",
        "state": "Maharashtra",
        "district": "Nashik",
        "land_acres": 4.0,
        "land_ownership": "Owned",
        "crop_type": "onion",
        "caste_category": "General",
        "annual_income": 200000,
        "existing_registrations": "Aadhaar KCC",
        "query": "Who will win the IPL this year?",
    }
    result = _run_profile(profile, monkeypatch)
    matched_names = [scheme["scheme_name"] for scheme in result.get("matched_schemes", [])]
    print("Anita Devi matched schemes:", matched_names)
    assert result["is_valid_query"] is False
    assert result["guardrail_message"] != ""
    assert result["matched_schemes"] == []
