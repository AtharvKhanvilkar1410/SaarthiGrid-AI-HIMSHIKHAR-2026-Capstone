"""CSV-backed retrieval utilities for SaarthiGrid AI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


STATE_ALIASES: dict[str, str] = {
    "hp": "himachal pradesh",
    "h.p.": "himachal pradesh",
    "himachal": "himachal pradesh",
    "himachal pradesh": "himachal pradesh",
    "pb": "punjab",
    "punjab": "punjab",
    "mh": "maharashtra",
    "maharashtra": "maharashtra",
}


def load_schemes(filepath: str) -> pd.DataFrame:
    """Load the scheme knowledge base from CSV.

    Args:
        filepath: Path to ``scheme_rules.csv``.

    Returns:
        A pandas DataFrame containing scheme rules with normalized missing values.
    """

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Scheme data file not found: {filepath}")
    df = pd.read_csv(path)
    required_columns = {
        "scheme_id",
        "scheme_name",
        "launched_by",
        "target_farmers",
        "min_land_acres",
        "max_land_acres",
        "eligible_crops",
        "eligible_states",
        "eligible_castes",
        "max_annual_income",
        "benefit_summary",
        "benefit_amount",
        "documents_required",
        "how_to_apply",
        "application_portal",
        "scheme_category",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Scheme data missing required columns: {sorted(missing_columns)}")
    return df.fillna("")


def _normalize_state(state: str) -> str:
    """Normalize state names and common abbreviations.

    Args:
        state: Raw state value from a farmer profile or scheme row.

    Returns:
        Lowercase canonical state name where known.
    """

    normalized = (state or "").strip().casefold()
    return STATE_ALIASES.get(normalized, normalized)


def _split_rule_values(value: Any) -> list[str]:
    """Split a comma-separated scheme rule field into normalized tokens.

    Args:
        value: Raw value from the CSV field.

    Returns:
        A list of lowercased tokens with surrounding whitespace removed.
    """

    return [token.strip().casefold() for token in str(value or "").split(",") if token.strip()]


def _matches_state(eligible_states: Any, farmer_state: str) -> bool:
    """Check whether a scheme is available in the farmer's state.

    Args:
        eligible_states: CSV value containing ``all`` or comma-separated states.
        farmer_state: Normalized farmer state.

    Returns:
        True when the scheme is state-compatible.
    """

    tokens = [_normalize_state(token) for token in _split_rule_values(eligible_states)]
    return "all" in tokens or farmer_state in tokens


def _matches_crop(eligible_crops: Any, farmer_crop: str) -> bool:
    """Check whether the farmer's crop matches the scheme's crop scope.

    Args:
        eligible_crops: CSV value containing ``all`` or comma-separated crops.
        farmer_crop: Lowercase crop from the farmer profile.

    Returns:
        True when the crop is covered by the scheme.
    """

    tokens = _split_rule_values(eligible_crops)
    if "all" in tokens:
        return True
    return any(farmer_crop == token or farmer_crop in token or token in farmer_crop for token in tokens)


def _matches_caste(eligible_castes: Any, farmer_caste: str) -> bool:
    """Check caste-category eligibility.

    Args:
        eligible_castes: CSV value containing ``all`` or comma-separated categories.
        farmer_caste: Farmer caste category.

    Returns:
        True when the farmer's caste category is allowed by the scheme row.
    """

    tokens = _split_rule_values(eligible_castes)
    return "all" in tokens or farmer_caste.casefold() in tokens


def filter_by_profile(df: pd.DataFrame, profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Filter schemes using deterministic eligibility fields from the profile.

    Args:
        df: Scheme rules DataFrame from :func:`load_schemes`.
        profile: Farmer profile dictionary with state, land, crop, caste, and income.

    Returns:
        List of matching scheme rows converted to dictionaries.
    """

    farmer_state = _normalize_state(str(profile.get("state", "")))
    farmer_crop = str(profile.get("crop_type", "")).strip().casefold()
    farmer_caste = str(profile.get("caste_category", "")).strip().casefold()
    land_acres = float(profile.get("land_acres", 0) or 0)
    annual_income = float(profile.get("annual_income", 0) or 0)

    matches: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        min_land = float(row["min_land_acres"])
        max_land = float(row["max_land_acres"])
        max_income = float(row["max_annual_income"])

        if not _matches_state(row["eligible_states"], farmer_state):
            continue
        if not min_land <= land_acres <= max_land:
            continue
        if not _matches_crop(row["eligible_crops"], farmer_crop):
            continue
        if not _matches_caste(row["eligible_castes"], farmer_caste):
            continue
        if annual_income > max_income:
            continue

        matches.append(row.to_dict())
    return matches


def format_scheme_for_llm(scheme: dict[str, Any]) -> str:
    """Format one scheme row as a compact evidence block for LLM prompts.

    Args:
        scheme: Scheme dictionary from the retriever.

    Returns:
        Multi-line string containing key scheme facts.
    """

    fields = [
        "scheme_id",
        "scheme_name",
        "launched_by",
        "target_farmers",
        "min_land_acres",
        "max_land_acres",
        "eligible_crops",
        "eligible_states",
        "eligible_castes",
        "max_annual_income",
        "benefit_summary",
        "benefit_amount",
        "documents_required",
        "how_to_apply",
        "application_portal",
        "scheme_category",
    ]
    return "\n".join(f"{field}: {scheme.get(field, '')}" for field in fields)
