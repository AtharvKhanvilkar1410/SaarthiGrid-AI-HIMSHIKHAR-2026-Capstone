"""Input and output guardrails for SaarthiGrid AI."""

from __future__ import annotations

import re
from typing import Any

from .prompts import GUARDRAIL_CHECK_PROMPT


BLOCKLIST: list[str] = [
    "cricket",
    "ipl",
    "bollywood",
    "election",
    "stock market",
    "sensex",
    "nifty",
    "politics",
    "party",
    "minister name checks",
]

FARMING_KEYWORDS: set[str] = {
    "farm",
    "farmer",
    "farming",
    "agriculture",
    "crop",
    "crops",
    "subsidy",
    "scheme",
    "schemes",
    "pm-kisan",
    "kisan",
    "soil",
    "irrigation",
    "horticulture",
    "livestock",
    "apple",
    "wheat",
    "rice",
    "maize",
    "onion",
    "insurance",
    "loan",
    "kcc",
}


def check_blocklist(query: str) -> bool:
    """Check whether a query contains a blocked off-domain term.

    Args:
        query: User query to inspect.

    Returns:
        True when a blocked term is present, otherwise False.
    """

    normalized_query = (query or "").casefold()
    return any(term.casefold() in normalized_query for term in BLOCKLIST)


def _heuristic_domain_check(query: str) -> bool:
    """Run a local farming-domain check when an LLM is unavailable.

    Args:
        query: User query to classify.

    Returns:
        True when the query is empty or appears related to farming and schemes.
    """

    normalized_query = (query or "").casefold()
    if not normalized_query.strip():
        return True
    return any(keyword in normalized_query for keyword in FARMING_KEYWORDS)


def check_with_llm(query: str, llm: Any) -> bool:
    """Ask an LLM whether the query is within the farming support domain.

    Args:
        query: User query to classify.
        llm: LangChain-compatible chat model with an ``invoke`` method.

    Returns:
        True when the LLM or fallback heuristic classifies the query as relevant.
    """

    if llm is None:
        return _heuristic_domain_check(query)

    prompt = GUARDRAIL_CHECK_PROMPT.format(query=query or "")
    try:
        response = llm.invoke(prompt)
        content = getattr(response, "content", str(response)).strip().upper()
        return content.startswith("YES")
    except Exception:
        return _heuristic_domain_check(query)


def validate_input(query: str, llm: Any) -> tuple[bool, str]:
    """Validate a raw user query before the agent pipeline continues.

    Args:
        query: User query to validate.
        llm: LangChain-compatible chat model or None.

    Returns:
        A tuple of ``(is_valid, message)``. The message is empty for valid input
        and contains a polite redirection for invalid input.
    """

    redirect_message = (
        "I can help with Indian farming, crop advisory, and government subsidy "
        "navigation. Please ask about your crop, land, irrigation, insurance, "
        "credit, livestock, or farmer scheme eligibility."
    )
    if check_blocklist(query):
        return False, redirect_message
    if not check_with_llm(query, llm):
        return False, redirect_message
    return True, ""


def validate_output(response: str) -> tuple[bool, str]:
    """Remove overconfident benefit guarantees from a generated response.

    Args:
        response: Model-generated response text.

    Returns:
        A tuple of ``(unchanged, sanitized_response)``. ``unchanged`` is False
        when the function had to hedge a risky guarantee.
    """

    sanitized = response or ""
    replacements = {
        r"\byou WILL receive\b": "you may receive after official approval",
        r"\byou will receive\b": "you may receive after official approval",
        r"\byou WILL get\b": "you may get after official approval",
        r"\byou will get\b": "you may get after official approval",
        r"\bwill be sanctioned\b": "may be sanctioned after official verification",
        r"\bguaranteed\b": "subject to official verification",
        r"\bguarantee\b": "officially verify",
    }
    for pattern, replacement in replacements.items():
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    return sanitized == (response or ""), sanitized
