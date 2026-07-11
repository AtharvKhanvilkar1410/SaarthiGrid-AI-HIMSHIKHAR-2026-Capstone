"""LangGraph node implementations for SaarthiGrid AI."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI

from .guardrails import validate_input, validate_output
from .prompts import (
    ELIGIBILITY_CHECK_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)
from .retriever import filter_by_profile, format_scheme_for_llm, load_schemes
from .state import AgentState


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PROFILE_FIELDS = [
    "name",
    "state",
    "district",
    "land_acres",
    "land_ownership",
    "crop_type",
    "caste_category",
    "annual_income",
    "existing_registrations",
]


def _resolve_project_path(path_value: str, default_relative_path: str) -> Path:
    """Resolve an environment path against the project root.

    Args:
        path_value: User-provided or environment-provided path.
        default_relative_path: Fallback path relative to the project root.

    Returns:
        Absolute Path object pointing inside or outside the project as requested.
    """

    raw_path = path_value or default_relative_path
    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _get_llm() -> ChatOpenAI | None:
    """Create a ChatOpenAI client when configuration is available.

    Args:
        None.

    Returns:
        A ChatOpenAI instance, or None when no API key is configured.
    """

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    try:
        temperature = float(os.getenv("TEMPERATURE", "0.1"))
    except ValueError:
        temperature = 0.1
    return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)


def _invoke_llm(llm: Any, prompt: str) -> str | None:
    """Invoke a LangChain chat model and return plain text.

    Args:
        llm: LangChain-compatible model or None.
        prompt: Prompt string to send to the model.

    Returns:
        Model response content, or None if no model is available or invocation fails.
    """

    if llm is None:
        return None
    try:
        response = llm.invoke(prompt)
        return getattr(response, "content", str(response))
    except Exception:
        return None


def _append_log(
    state: AgentState,
    step: str,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> AgentState:
    """Append an auditable step entry to the agent state.

    Args:
        state: Current graph state.
        step: Node or action name.
        message: Human-readable step summary.
        metadata: Optional structured metadata for debugging.

    Returns:
        Updated state with the new log entry.
    """

    updated_state: AgentState = dict(state)
    log = list(updated_state.get("agent_log", []))
    log.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "message": message,
            "metadata": metadata or {},
        }
    )
    updated_state["agent_log"] = log
    return updated_state


def _parse_json_object(raw_text: str | None) -> dict[str, Any] | None:
    """Parse the first JSON object found in a model response.

    Args:
        raw_text: Raw model response text.

    Returns:
        Parsed JSON dictionary, or None when parsing fails.
    """

    if not raw_text:
        return None
    text = raw_text.strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        text = match.group(0)
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        relaxed_text = re.sub(r"'", '"', text)
        try:
            parsed = json.loads(relaxed_text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


def _documents_list(documents_required: str) -> list[str]:
    """Convert a CSV document field into a clean list.

    Args:
        documents_required: Comma-separated document text from the scheme CSV.

    Returns:
        List of document names.
    """

    return [item.strip() for item in str(documents_required or "").split(",") if item.strip()]


def _fallback_eligibility(
    scheme: dict[str, Any],
    profile: dict[str, Any],
    structured_query: str,
) -> dict[str, Any]:
    """Create deterministic eligibility reasoning when an LLM is unavailable.

    Args:
        scheme: Matched scheme dictionary.
        profile: Farmer profile dictionary.
        structured_query: Structured farmer profile sentence.

    Returns:
        Eligibility result dictionary with verdict, reason, and confidence.
    """

    del structured_query
    scheme_name = str(scheme.get("scheme_name", "Unknown Scheme"))
    category = str(scheme.get("scheme_category", "")).casefold()
    ownership = str(profile.get("land_ownership", "")).casefold()

    if "pm-kisan" in scheme_name.casefold() and ownership == "leased":
        verdict = "NOT_ELIGIBLE"
        reason = "PM-KISAN requires landholding farmer-family records; a leased profile needs ownership verification and may not qualify directly."
        confidence = "HIGH"
    elif "maan dhan" in scheme_name.casefold() and ownership == "leased":
        verdict = "NOT_ELIGIBLE"
        reason = "PM-KMY is for small and marginal landholding farmers, so leased land without landholding records does not directly satisfy the rule."
        confidence = "HIGH"
    elif category in {"credit", "insurance", "infrastructure", "irrigation", "protected_cultivation", "crop_protection", "horticulture", "livestock"}:
        verdict = "PARTIAL"
        reason = "The profile matches the basic rule filters, but final eligibility depends on official verification, notified components, bank sanction, or district targets."
        confidence = "MEDIUM"
    elif category == "pension":
        verdict = "PARTIAL"
        reason = "The land-size rule matches, but age between 18 and 40 years must be verified for PM-KMY enrollment."
        confidence = "MEDIUM"
    else:
        verdict = "ELIGIBLE"
        reason = "The farmer profile matches the state, crop, caste, land and income rules available in the scheme database."
        confidence = "HIGH"

    return {
        "scheme_name": scheme_name,
        "verdict": verdict,
        "reason": reason,
        "confidence": confidence,
    }


def _fallback_card(
    scheme: dict[str, Any],
    eligibility: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Build a farmer-facing response card without an LLM.

    Args:
        scheme: Scheme dictionary.
        eligibility: Eligibility result dictionary.
        profile: Farmer profile dictionary.

    Returns:
        Structured response card suitable for Streamlit rendering.
    """

    farmer_name = str(profile.get("name", "the farmer")).strip() or "the farmer"
    next_step = str(scheme.get("how_to_apply", "")).strip()
    if not next_step:
        next_step = "Contact the nearest Agriculture or Horticulture Department office for the current application window."
    return {
        "scheme_name": str(scheme.get("scheme_name", eligibility.get("scheme_name", "Scheme"))),
        "what_you_get": str(scheme.get("benefit_summary", "")).strip(),
        "eligibility_summary": (
            f"{farmer_name} {eligibility.get('reason', 'matches the available scheme rules.')} "
            "Final approval remains subject to official verification."
        ),
        "documents_needed": _documents_list(str(scheme.get("documents_required", ""))),
        "exact_next_step": next_step,
        "portal_or_office": str(scheme.get("application_portal", "")).strip(),
    }


def _fallback_no_scheme_response(structured_query: str) -> str:
    """Create a safe no-match response when no scheme passes deterministic filters.

    Args:
        structured_query: Structured farmer profile sentence.

    Returns:
        Farmer-friendly fallback message.
    """

    return (
        "No scheme in the current SaarthiGrid rule base matched this profile exactly. "
        f"Profile checked: {structured_query} "
        "Please verify with the nearest Agriculture or Horticulture Department office because "
        "district targets, annual action plans, and application windows can change. Adding details "
        "about irrigation need, livestock interest, equipment requirement, or post-harvest plans may "
        "help identify a more specific scheme."
    )


def _sanitize_card(card: dict[str, Any]) -> dict[str, Any]:
    """Apply output guardrails to a response card.

    Args:
        card: Structured response card.

    Returns:
        Sanitized card with overconfident language hedged.
    """

    sanitized_card = dict(card)
    for key in ("what_you_get", "eligibility_summary", "exact_next_step"):
        _, sanitized_text = validate_output(str(sanitized_card.get(key, "")))
        sanitized_card[key] = sanitized_text
    documents = sanitized_card.get("documents_needed", [])
    if not isinstance(documents, list):
        sanitized_card["documents_needed"] = _documents_list(str(documents))
    return sanitized_card


def guardrail_node(state: AgentState) -> AgentState:
    """Validate whether the query belongs to the SaarthiGrid farming domain.

    Args:
        state: Current AgentState with ``raw_query``.

    Returns:
        Updated AgentState containing guardrail decision and log entry.
    """

    updated_state: AgentState = dict(state)
    raw_query = str(updated_state.get("raw_query", "") or "")
    llm = _get_llm()
    is_valid, message = validate_input(raw_query, llm)
    updated_state["is_valid_query"] = is_valid
    updated_state["guardrail_message"] = message

    if not is_valid:
        updated_state["matched_schemes"] = []
        updated_state["eligibility_results"] = []
        updated_state["final_response"] = message

    return _append_log(
        updated_state,
        "guardrail_node",
        "Query accepted for farming-domain processing." if is_valid else "Query blocked by guardrails.",
        {"is_valid_query": is_valid, "raw_query": raw_query},
    )


def profile_parser_node(state: AgentState) -> AgentState:
    """Validate profile fields and build a structured query sentence.

    Args:
        state: Current AgentState with ``farmer_profile``.

    Returns:
        Updated AgentState containing ``structured_query`` or an error message.
    """

    updated_state: AgentState = dict(state)
    profile = dict(updated_state.get("farmer_profile", {}))
    missing_fields = [
        field
        for field in REQUIRED_PROFILE_FIELDS
        if profile.get(field) is None or str(profile.get(field)).strip() == ""
    ]

    if missing_fields:
        error_message = f"Missing required farmer profile fields: {', '.join(missing_fields)}"
        updated_state["error"] = error_message
        updated_state["structured_query"] = ""
        updated_state["final_response"] = error_message
        return _append_log(
            updated_state,
            "profile_parser_node",
            "Profile validation failed.",
            {"missing_fields": missing_fields},
        )

    structured_query = (
        f"Farmer from {profile['state']}, {profile['district']}. "
        f"Land: {float(profile['land_acres']):g} acres ({profile['land_ownership']}). "
        f"Crop: {profile['crop_type']}. Caste: {profile['caste_category']}. "
        f"Income: ₹{int(float(profile['annual_income']))}/year. "
        f"Registrations: {profile['existing_registrations']}."
    )
    updated_state["structured_query"] = structured_query
    return _append_log(
        updated_state,
        "profile_parser_node",
        "Farmer profile parsed into structured query.",
        {"structured_query": structured_query},
    )


def scheme_matcher_node(state: AgentState) -> AgentState:
    """Match the farmer profile against the CSV scheme rule base.

    Args:
        state: Current AgentState with parsed profile details.

    Returns:
        Updated AgentState containing matched scheme dictionaries.
    """

    updated_state: AgentState = dict(state)
    if updated_state.get("error"):
        return _append_log(updated_state, "scheme_matcher_node", "Skipped because profile parsing failed.")

    scheme_path = _resolve_project_path(
        os.getenv("SCHEME_DATA_PATH", ""),
        "data/scheme_rules.csv",
    )
    try:
        df = load_schemes(str(scheme_path))
        matches = filter_by_profile(df, dict(updated_state.get("farmer_profile", {})))
    except Exception as exc:
        updated_state["matched_schemes"] = []
        updated_state["error"] = str(exc)
        updated_state["final_response"] = "The scheme database could not be loaded. Please check the data file path."
        return _append_log(
            updated_state,
            "scheme_matcher_node",
            "Scheme matching failed.",
            {"error": str(exc), "scheme_path": str(scheme_path)},
        )

    updated_state["matched_schemes"] = matches
    if not matches:
        updated_state["final_response"] = _fallback_no_scheme_response(
            str(updated_state.get("structured_query", ""))
        )

    return _append_log(
        updated_state,
        "scheme_matcher_node",
        f"Matched {len(matches)} schemes from rule base.",
        {"match_count": len(matches), "scheme_names": [row.get("scheme_name") for row in matches]},
    )


def eligibility_checker_node(state: AgentState) -> AgentState:
    """Classify matched schemes as eligible, partial, or not eligible.

    Args:
        state: Current AgentState with ``matched_schemes`` and ``structured_query``.

    Returns:
        Updated AgentState containing ``eligibility_results``.
    """

    updated_state: AgentState = dict(state)
    matched_schemes = list(updated_state.get("matched_schemes", []))
    if not matched_schemes or updated_state.get("error"):
        updated_state["eligibility_results"] = []
        return _append_log(
            updated_state,
            "eligibility_checker_node",
            "No matched schemes available for eligibility checking.",
        )

    llm = _get_llm()
    profile = dict(updated_state.get("farmer_profile", {}))
    structured_query = str(updated_state.get("structured_query", ""))
    eligibility_results: list[dict[str, Any]] = []

    for scheme in matched_schemes:
        scheme_details = format_scheme_for_llm(scheme)
        prompt = ELIGIBILITY_CHECK_PROMPT.format(
            structured_query=structured_query,
            scheme_details=scheme_details,
        )
        parsed = _parse_json_object(_invoke_llm(llm, prompt))
        if not parsed:
            parsed = _fallback_eligibility(scheme, profile, structured_query)

        verdict = str(parsed.get("verdict", "PARTIAL")).upper()
        if verdict not in {"ELIGIBLE", "PARTIAL", "NOT_ELIGIBLE"}:
            verdict = "PARTIAL"
        confidence = str(parsed.get("confidence", "MEDIUM")).upper()
        if confidence not in {"HIGH", "MEDIUM", "LOW"}:
            confidence = "MEDIUM"

        result = {
            "scheme_id": scheme.get("scheme_id", ""),
            "scheme_name": str(parsed.get("scheme_name") or scheme.get("scheme_name", "")),
            "verdict": verdict,
            "reason": str(parsed.get("reason", "")),
            "confidence": confidence,
            "_scheme_details": scheme,
        }
        eligibility_results.append(result)

    updated_state["eligibility_results"] = eligibility_results
    return _append_log(
        updated_state,
        "eligibility_checker_node",
        f"Generated eligibility verdicts for {len(eligibility_results)} schemes.",
        {
            "eligible_or_partial": [
                result["scheme_name"]
                for result in eligibility_results
                if result["verdict"] in {"ELIGIBLE", "PARTIAL"}
            ]
        },
    )


def response_generator_node(state: AgentState) -> AgentState:
    """Generate farmer-friendly final guidance and structured UI cards.

    Args:
        state: Current AgentState with eligibility results.

    Returns:
        Updated AgentState with ``final_response`` and enriched eligibility cards.
    """

    updated_state: AgentState = dict(state)
    if updated_state.get("error"):
        return _append_log(updated_state, "response_generator_node", "Skipped because an earlier error exists.")

    eligibility_results = list(updated_state.get("eligibility_results", []))
    actionable_results = [
        result for result in eligibility_results if result.get("verdict") in {"ELIGIBLE", "PARTIAL"}
    ]
    if not actionable_results:
        updated_state["final_response"] = (
            "I found no directly actionable scheme for this profile from the current rule base. "
            "Please verify with the nearest Agriculture or Horticulture Department office because "
            "district targets and annual action plans can change."
        )
        return _append_log(
            updated_state,
            "response_generator_node",
            "No eligible or partial schemes available for response generation.",
        )

    llm = _get_llm()
    structured_query = str(updated_state.get("structured_query", ""))
    profile = dict(updated_state.get("farmer_profile", {}))
    response_cards: list[dict[str, Any]] = []
    enriched_results: list[dict[str, Any]] = []

    for result in eligibility_results:
        enriched_result = dict(result)
        if result.get("verdict") in {"ELIGIBLE", "PARTIAL"}:
            scheme = dict(result.get("_scheme_details", {}))
            prompt = RESPONSE_GENERATION_PROMPT.format(
                name=result.get("scheme_name", ""),
                profile=structured_query,
                scheme_details=format_scheme_for_llm(scheme),
                verdict=result.get("verdict", ""),
                reason=result.get("reason", ""),
            )
            parsed_card = _parse_json_object(_invoke_llm(llm, prompt))
            if not parsed_card:
                parsed_card = _fallback_card(scheme, result, profile)
            card = _sanitize_card(parsed_card)
            enriched_result["farmer_response"] = card
            response_cards.append(card)
        enriched_results.append(enriched_result)

    lines = [
        "SaarthiGrid AI scheme guidance",
        f"Profile: {structured_query}",
        "",
        f"Found {len(response_cards)} schemes that look eligible or partially eligible, subject to official verification.",
    ]
    for index, card in enumerate(response_cards, start=1):
        lines.extend(
            [
                "",
                f"{index}. {card.get('scheme_name', 'Scheme')}",
                f"What you may get: {card.get('what_you_get', '')}",
                f"Eligibility summary: {card.get('eligibility_summary', '')}",
                "Documents needed: " + ", ".join(card.get("documents_needed", [])),
                f"Next step: {card.get('exact_next_step', '')}",
                f"Portal or office: {card.get('portal_or_office', '')}",
            ]
        )

    _, sanitized_response = validate_output("\n".join(lines))
    updated_state["eligibility_results"] = enriched_results
    updated_state["final_response"] = sanitized_response
    return _append_log(
        updated_state,
        "response_generator_node",
        f"Generated {len(response_cards)} farmer-facing response cards.",
        {"response_card_count": len(response_cards)},
    )


def logger_node(state: AgentState) -> AgentState:
    """Persist an audit log for the complete agent run.

    Args:
        state: Final AgentState after response generation.

    Returns:
        AgentState with logger step appended.
    """

    updated_state: AgentState = dict(state)
    agent_log = list(updated_state.get("agent_log", []))
    started_at = time.time()
    if agent_log:
        try:
            first_timestamp = datetime.fromisoformat(str(agent_log[0]["timestamp"]))
            started_at = first_timestamp.timestamp()
        except Exception:
            started_at = time.time()
    processing_time_ms = int((time.time() - started_at) * 1000)

    profile = dict(updated_state.get("farmer_profile", {}))
    eligible_schemes = [
        result.get("scheme_name", "")
        for result in updated_state.get("eligibility_results", [])
        if result.get("verdict") in {"ELIGIBLE", "PARTIAL"}
    ]
    log_path = _resolve_project_path(os.getenv("LOG_FILE_PATH", ""), "logs/agent_log.json")
    updated_state = _append_log(
        updated_state,
        "logger_node",
        "Persisted run log.",
        {"log_path": str(log_path), "processing_time_ms": processing_time_ms},
    )
    agent_log = list(updated_state.get("agent_log", []))

    run_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "farmer_name": profile.get("name", ""),
        "state": profile.get("state", ""),
        "schemes_matched": len(updated_state.get("matched_schemes", [])),
        "eligible_schemes": eligible_schemes,
        "processing_time_ms": processing_time_ms,
        "agent_steps": agent_log,
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing_records: list[dict[str, Any]]
    if log_path.exists():
        try:
            loaded = json.loads(log_path.read_text(encoding="utf-8"))
            existing_records = loaded if isinstance(loaded, list) else [loaded]
        except json.JSONDecodeError:
            existing_records = []
    else:
        existing_records = []

    existing_records.append(run_record)
    log_path.write_text(json.dumps(existing_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "SaarthiGrid run complete: "
        f"{profile.get('name', 'Unknown farmer')} | "
        f"{len(updated_state.get('matched_schemes', []))} matched | "
        f"{len(eligible_schemes)} actionable"
    )

    return updated_state
