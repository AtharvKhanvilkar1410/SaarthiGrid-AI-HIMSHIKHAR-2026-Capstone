"""Streamlit interface for SaarthiGrid AI."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:

    def load_dotenv(dotenv_path: Path) -> bool:
        """Load simple KEY=VALUE pairs when python-dotenv is unavailable.

        Args:
            dotenv_path: Path to the local environment file.

        Returns:
            True when a file was found and parsed, otherwise False.
        """

        if not dotenv_path.exists():
            return False
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", maxsplit=1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return True


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[0]
for import_path in (PROJECT_ROOT, APP_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

load_dotenv(PROJECT_ROOT / ".env")

from pages.how_it_works import render as render_how_it_works  # noqa: E402
from src.agent import app_graph  # noqa: E402


CENTRAL_SCHEMES = [
    "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
    "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
    "PM Kisan Maan Dhan Yojana",
    "Kisan Credit Card (KCC)",
    "Soil Health Card Scheme",
    "PMKSY (Pradhan Mantri Krishi Sinchayee Yojana)",
    "eNAM (National Agriculture Market)",
    "Agriculture Infrastructure Fund (AIF)",
    "PKVY (Paramparagat Krishi Vikas Yojana)",
    "MIDH (Mission for Integrated Development of Horticulture)",
    "RKVY (Rashtriya Krishi Vikas Yojana)",
    "National Livestock Mission",
    "National Food Security Mission (NFSM)",
    "NMSA (National Mission for Sustainable Agriculture)",
    "Sub-Mission on Agricultural Mechanization (SMAM)",
]

HIMACHAL_SCHEMES = [
    "HP Prakritik Kheti Khushhal Kisan Yojana",
    "Mukhyamantri Khet Sanrakshan Yojana",
    "HP Horticulture Development Scheme",
    "HP Beekeeping Development Scheme",
    "HP Polyhouse / Protected Cultivation Subsidy",
    "HP Irrigation Subsidy Scheme",
    "HP SC/ST Farmer Equipment Subsidy",
    "HP Seed Subsidy Scheme",
    "HP Sheep and Goat Rearing Subsidy",
    "HP Mushroom Cultivation Scheme",
]


def build_initial_state(profile: dict[str, Any], raw_query: str) -> dict[str, Any]:
    """Build the initial LangGraph state from Streamlit inputs.

    Args:
        profile: Farmer profile dictionary from the form.
        raw_query: User query or default scheme-search query.

    Returns:
        Initial state dictionary for the graph invocation.
    """

    return {
        "farmer_profile": profile,
        "raw_query": raw_query,
        "is_valid_query": False,
        "guardrail_message": "",
        "structured_query": "",
        "matched_schemes": [],
        "eligibility_results": [],
        "final_response": "",
        "agent_log": [],
        "error": "",
    }


def verdict_badge(verdict: str) -> tuple[str, str, str]:
    """Return the icon, background, and text color for a verdict.

    Args:
        verdict: Eligibility verdict string.

    Returns:
        Tuple containing an emoji icon, CSS background, and CSS text color.
    """

    normalized = (verdict or "").upper()
    if normalized == "ELIGIBLE":
        return "✅", "#064e3b", "#10b981"
    if normalized == "PARTIAL":
        return "⚠️", "#451a03", "#f59e0b"
    return "❌", "#1f0000", "#ef4444"


def safe_html(value: Any) -> str:
    """Escape a value before including it in HTML rendered by Streamlit.

    Args:
        value: Arbitrary value to convert to safe display text.

    Returns:
        HTML-escaped string.
    """

    return escape(str(value or ""))


def is_himachal_scheme(result: dict[str, Any]) -> bool:
    """Detect whether an eligibility result came from a Himachal scheme.

    Args:
        result: Eligibility result that may include scheme details.

    Returns:
        True when the scheme source is Himachal Pradesh, otherwise False.
    """

    scheme = dict(result.get("_scheme_details", {}) or {})
    eligible_states = str(scheme.get("eligible_states", "")).strip().casefold()
    launched_by = str(scheme.get("launched_by", "")).strip().casefold()
    scheme_id = str(scheme.get("scheme_id", "")).strip().casefold()
    return (
        eligible_states == "himachal pradesh"
        or "government of himachal pradesh" in launched_by
        or scheme_id.startswith("hp_")
    )


def should_display_scheme_for_state(result: dict[str, Any], farmer_state: str) -> bool:
    """Decide whether a scheme card should be visible for the selected state.

    Args:
        result: Eligibility result for a central or state scheme.
        farmer_state: State selected by the farmer in the UI.

    Returns:
        False for an HP-only scheme shown to a non-HP farmer, otherwise True.
    """

    if is_himachal_scheme(result) and farmer_state.strip().casefold() != "himachal pradesh":
        return False
    return True


def documents_for_result(result: dict[str, Any]) -> list[str]:
    """Extract a normalized document checklist from a result.

    Args:
        result: Eligibility result with optional farmer response and scheme data.

    Returns:
        Clean list of document names.
    """

    response = result.get("farmer_response", {})
    card = dict(response) if isinstance(response, dict) else {}
    documents = card.get("documents_needed", [])
    if isinstance(documents, list):
        cleaned = [str(document).strip() for document in documents if str(document).strip()]
        if cleaned:
            return cleaned
    elif str(documents).strip():
        return [item.strip() for item in str(documents).split(",") if item.strip()]

    scheme = dict(result.get("_scheme_details", {}) or {})
    return [
        item.strip()
        for item in str(scheme.get("documents_required", "")).split(",")
        if item.strip()
    ]


def scheme_card_data(result: dict[str, Any]) -> dict[str, Any]:
    """Resolve all presentation fields for a scheme card.

    Args:
        result: Eligibility result from the agent.

    Returns:
        Dictionary containing complete card display fields.
    """

    response = result.get("farmer_response", {})
    card = dict(response) if isinstance(response, dict) else {}
    scheme = dict(result.get("_scheme_details", {}) or {})

    return {
        "scheme_name": str(result.get("scheme_name") or scheme.get("scheme_name") or "Government Scheme"),
        "what_you_get": str(
            card.get("what_you_get")
            or scheme.get("benefit_summary")
            or "Benefit details should be confirmed with the implementing department."
        ),
        "eligibility_summary": str(
            card.get("eligibility_summary")
            or result.get("reason")
            or "Final eligibility is subject to verification by the responsible authority."
        ),
        "documents_needed": documents_for_result(result),
        "exact_next_step": str(
            card.get("exact_next_step")
            or scheme.get("how_to_apply")
            or "Contact the nearest Agriculture Department office for current application guidance."
        ),
        "portal_or_office": str(
            card.get("portal_or_office")
            or scheme.get("application_portal")
            or "Nearest Agriculture Department office"
        ),
    }


def generate_report_text(
    results: list[dict[str, Any]],
    farmer_profile: dict[str, Any],
) -> str:
    """Create a downloadable plain-text farmer scheme report.

    Args:
        results: Eligibility results to include in the report.
        farmer_profile: Farmer profile used to generate the matches.

    Returns:
        Complete plain-text report containing profile, verdicts, documents, and actions.
    """

    generated_at = datetime.now().astimezone().strftime("%d %B %Y, %I:%M %p %Z")
    registrations = farmer_profile.get("existing_registrations", "none")
    if isinstance(registrations, list):
        registrations = ", ".join(str(item) for item in registrations) or "none"

    lines = [
        "SAARTHIGRID AI - PERSONAL SCHEME REPORT",
        "=" * 48,
        f"Generated at: {generated_at}",
        "",
        "FARMER PROFILE",
        "-" * 48,
        f"Name: {farmer_profile.get('name', '')}",
        f"State: {farmer_profile.get('state', '')}",
        f"District: {farmer_profile.get('district', '')}",
        (
            f"Land: {farmer_profile.get('land_acres', '')} acres "
            f"({farmer_profile.get('land_ownership', '')})"
        ),
        f"Primary crop: {farmer_profile.get('crop_type', '')}",
        f"Caste category: {farmer_profile.get('caste_category', '')}",
        f"Annual income: ₹{farmer_profile.get('annual_income', '')}",
        f"Existing registrations: {registrations}",
        "",
        f"MATCHED SCHEMES ({len(results)})",
        "=" * 48,
    ]

    if not results:
        lines.extend(
            [
                "No scheme in the current knowledge base matched this profile.",
                "Please verify current district programmes with the nearest Agriculture Department office.",
            ]
        )

    for index, result in enumerate(results, start=1):
        card = scheme_card_data(result)
        documents = card["documents_needed"]
        lines.extend(
            [
                "",
                f"{index}. {card['scheme_name']}",
                f"Eligibility: {str(result.get('verdict', 'PARTIAL')).replace('_', ' ')}",
                f"Reason: {result.get('reason') or card['eligibility_summary']}",
                f"What you may get: {card['what_you_get']}",
                "Documents needed:",
            ]
        )
        if documents:
            lines.extend(f"  - {document}" for document in documents)
        else:
            lines.append("  - Confirm the latest checklist with the implementing office.")
        lines.extend(
            [
                f"Next step: {card['exact_next_step']}",
                f"Portal or office: {card['portal_or_office']}",
            ]
        )

    lines.extend(
        [
            "",
            "-" * 48,
            "Guidance only. Final eligibility and approval are determined by official government bodies.",
            "Generated by SaarthiGrid AI | HIMSHIKHAR 2026 AAI Capstone",
        ]
    )
    return "\n".join(lines)


def render_hero() -> None:
    """Render the product hero banner.

    Args:
        None.

    Returns:
        None.
    """

    st.markdown(
        """<div class="saarthi-hero">
            <div class="saarthi-hero-copy">
                <h1>🌾 SaarthiGrid AI</h1>
                <h3>Your Personal Farmer Subsidy Navigator</h3>
                <p>Powered by LangGraph + RAG · 25 Government Schemes · AI Eligibility Matching</p>
                <div class="hero-badges">
                    <span>✅ 25 Schemes</span>
                    <span>🏛️ Central + HP</span>
                    <span>🤖 AI-Powered</span>
                </div>
            </div>
            <div class="saarthi-hero-visual" aria-hidden="true">🌱</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_stats_bar() -> None:
    """Render the four product coverage metrics below the hero.

    Args:
        None.

    Returns:
        None.
    """

    metrics = [
        ("🏛️", "25", "Government Schemes"),
        ("🌾", "15+", "Crop Types Covered"),
        ("📍", "10+", "States Supported"),
        ("⚡", "&lt;3s", "Avg Response Time"),
    ]
    columns = st.columns(4, gap="medium")
    for column, (icon, number, label) in zip(columns, metrics):
        with column:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-number">{number}</div>
                    <div class="metric-label">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_get_started_guide() -> None:
    """Render the three-step onboarding guide before the first search.

    Args:
        None.

    Returns:
        None.
    """

    st.markdown("### 🚀 Get Started in 3 Steps")
    steps = [
        (
            "①",
            "📋",
            "Fill Your Profile",
            "Enter your state, land size, crop type, caste, and income in the sidebar form",
        ),
        (
            "②",
            "🤖",
            "AI Scans Schemes",
            "Our LangGraph agent checks 25 schemes and verifies your eligibility using GPT-4o-mini",
        ),
        (
            "③",
            "📋",
            "Get Your Action Plan",
            "Receive matched schemes, document checklist, and exact next steps — tailored to you",
        ),
    ]
    columns = st.columns(3, gap="large")
    for column, (number, icon, title, description) in zip(columns, steps):
        with column:
            st.markdown(
                f"""<div class="step-card">
                    <div class="step-top">
                        <span class="step-number">{number}</span>
                        <span class="step-icon">{icon}</span>
                    </div>
                    <div class="step-title">{title}</div>
                    <div class="step-text">{description}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_scheme_list(schemes: list[str]) -> None:
    """Render a styled list of scheme names.

    Args:
        schemes: Ordered scheme names to display.

    Returns:
        None.
    """

    rows = "".join(
        f'<div class="scheme-list-row"><span>✅</span><span>{safe_html(scheme)}</span></div>'
        for scheme in schemes
    )
    st.markdown(f'<div class="scheme-list">{rows}</div>', unsafe_allow_html=True)


def render_scheme_preview() -> None:
    """Render the central and Himachal scheme catalogue preview.

    Args:
        None.

    Returns:
        None.
    """

    st.markdown("### 📚 Schemes We Cover")
    central_column, himachal_column = st.columns(2, gap="large")
    with central_column:
        with st.expander("🏛️ Central Government Schemes (15)", expanded=False):
            render_scheme_list(CENTRAL_SCHEMES)
    with himachal_column:
        with st.expander("🏔️ Himachal Pradesh Schemes (10)", expanded=False):
            render_scheme_list(HIMACHAL_SCHEMES)
    st.info(
        "💡 Pro Tip: Farmers in Himachal Pradesh may qualify for BOTH central and state schemes — "
        "up to 20+ schemes in a single query!"
    )


def mark_search_started() -> None:
    """Mark a form submission before Streamlit begins its full rerun.

    Args:
        None.

    Returns:
        None.
    """

    st.session_state["results"] = st.session_state.get("last_result", {})


def render_profile_form() -> tuple[bool, dict[str, Any], str]:
    """Render the farmer profile form in the Find My Schemes tab.

    Args:
        None.

    Returns:
        Tuple containing submit status, farmer profile, and raw query.
    """

    with st.form("farmer_profile_form"):
        st.header("Your Farm Profile")
        st.caption("Tell us about your farm so the agent can apply the right scheme rules.")
        name = st.text_input("Name", value="Ramesh Kumar")
        state = st.selectbox(
            "State",
            [
                "Himachal Pradesh",
                "Punjab",
                "Maharashtra",
                "Haryana",
                "Uttar Pradesh",
                "Uttarakhand",
                "Rajasthan",
                "Madhya Pradesh",
                "Bihar",
                "Karnataka",
            ],
        )
        district = st.text_input("District", value="Mandi")
        land_acres = st.number_input(
            "Land size in acres",
            min_value=0.1,
            max_value=100.0,
            value=1.5,
            step=0.1,
        )
        land_ownership = st.radio(
            "Land ownership",
            ["Owned", "Leased"],
            horizontal=True,
        )
        crop_type = st.text_input(
            "Primary crop",
            value="wheat",
            placeholder="e.g., wheat, apple, rice, onion",
        )
        caste_category = st.selectbox(
            "Caste category",
            ["General", "SC", "ST", "OBC"],
        )
        annual_income = st.number_input(
            "Annual income ₹",
            min_value=0,
            value=60000,
            step=5000,
        )
        existing_registrations = st.multiselect(
            "Existing registrations",
            ["Aadhaar", "PM-KISAN", "KCC", "Soil Health Card", "eNAM", "FPO"],
        )
        optional_query = st.text_area(
            "Optional query",
            placeholder=(
                "Tell us what support you need: insurance, irrigation, equipment, "
                "crop advisory..."
            ),
        )
        submitted = st.form_submit_button(
            "🔍 Find My Schemes",
            use_container_width=True,
            on_click=mark_search_started,
        )

    registrations_text = " ".join(existing_registrations) if existing_registrations else "none"
    query = optional_query.strip() or f"Find government farmer schemes for {crop_type} farming."
    farmer_profile = {
        "name": name.strip(),
        "state": state,
        "district": district.strip(),
        "land_acres": float(land_acres),
        "land_ownership": land_ownership,
        "crop_type": crop_type.strip(),
        "caste_category": caste_category,
        "annual_income": int(annual_income),
        "existing_registrations": registrations_text,
        "query": query,
    }
    return submitted, farmer_profile, query


def run_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    """Invoke the SaarthiGrid LangGraph agent and persist UI state.

    Args:
        profile: Farmer profile dictionary.
        query: Raw user query.

    Returns:
        Final agent state returned by LangGraph.
    """

    result = app_graph.invoke(build_initial_state(profile, query))
    st.session_state["last_result"] = result
    st.session_state["results"] = result
    st.session_state["last_profile"] = profile
    st.session_state["agent_log"] = result.get("agent_log", [])
    return result


def render_scheme_card(result: dict[str, Any]) -> None:
    """Render one complete scheme result inside an expander.

    Args:
        result: Eligibility result enriched with farmer-facing response data.

    Returns:
        None.
    """

    verdict = str(result.get("verdict", "PARTIAL")).upper()
    if verdict not in {"ELIGIBLE", "PARTIAL", "NOT_ELIGIBLE"}:
        verdict = "PARTIAL"
    icon, badge_background, badge_color = verdict_badge(verdict)
    card = scheme_card_data(result)
    documents = card["documents_needed"]
    documents_html = "".join(f"<li>{safe_html(document)}</li>" for document in documents)
    if not documents_html:
        documents_html = "<li>Confirm the latest checklist with the implementing office.</li>"

    portal = str(card["portal_or_office"]).strip()
    if portal.casefold().startswith(("https://", "http://")):
        portal_html = (
            f'<a class="scheme-apply" href="{escape(portal, quote=True)}" '
            'target="_blank" rel="noopener noreferrer">Apply Here →</a>'
        )
    else:
        portal_html = (
            '<div class="scheme-office"><span>Application point:</span> '
            f"{safe_html(portal)}</div>"
        )

    expander_label = f"{icon} {card['scheme_name']} · {verdict.replace('_', ' ').title()}"
    with st.expander(expander_label, expanded=False):
        st.markdown(
            f"""<div class="scheme-card-body">
                <div class="scheme-card-head">
                    <div class="scheme-card-name">{safe_html(card['scheme_name'])}</div>
                    <span class="verdict-pill" style="background:{badge_background};color:{badge_color};">
                        {icon} {safe_html(verdict.replace('_', ' '))}
                    </span>
                </div>
                <div class="scheme-card-section">
                    <div class="scheme-card-label">💰 What You Get</div>
                    <p>{safe_html(card['what_you_get'])}</p>
                </div>
                <div class="scheme-card-section eligibility-note">
                    <div class="scheme-card-label">🔎 Why This Verdict</div>
                    <p>{safe_html(card['eligibility_summary'])}</p>
                </div>
                <div class="scheme-card-section">
                    <div class="scheme-card-label">📋 Documents Needed</div>
                    <ul>{documents_html}</ul>
                </div>
                <div class="scheme-card-section next-step-section">
                    <div class="scheme-card-label">🎯 Your Next Step</div>
                    <p><strong>{safe_html(card['exact_next_step'])}</strong></p>
                </div>
                <div class="scheme-card-action">🌐 {portal_html}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_result_collection(
    results: list[dict[str, Any]],
    empty_message: str,
) -> None:
    """Render a collection of scheme cards or an empty-state message.

    Args:
        results: Scheme results to render.
        empty_message: Message shown when the collection is empty.

    Returns:
        None.
    """

    if not results:
        st.info(empty_message)
        return
    for result in results:
        render_scheme_card(result)


def render_application_guide(eligible_results: list[dict[str, Any]]) -> None:
    """Render consolidated next steps for all eligible schemes.

    Args:
        eligible_results: Results with an ELIGIBLE verdict.

    Returns:
        None.
    """

    if not eligible_results:
        st.info(
            "No fully eligible scheme is available for a consolidated application plan. "
            "Review the Partial tab for schemes that need additional verification."
        )
        return

    list_items: list[str] = []
    for result in eligible_results:
        card = scheme_card_data(result)
        portal = str(card["portal_or_office"]).strip()
        if portal.casefold().startswith(("https://", "http://")):
            portal_html = (
                f'<a href="{escape(portal, quote=True)}" target="_blank" '
                'rel="noopener noreferrer">Open official portal →</a>'
            )
        else:
            portal_html = f"<span>{safe_html(portal)}</span>"
        list_items.append(
            f"""<li>
                <div class="apply-guide-name">{safe_html(card['scheme_name'])}</div>
                <p>{safe_html(card['exact_next_step'])}</p>
                <div class="apply-guide-link">{portal_html}</div>
            </li>"""
        )

    st.markdown(
        '<div class="apply-guide-intro">Your consolidated application sequence</div>'
        f'<ol class="apply-guide">{"".join(list_items)}</ol>',
        unsafe_allow_html=True,
    )


def render_result_summary(
    count: int,
    eligible_count: int,
    partial_count: int,
    not_eligible_count: int,
    farmer_profile: dict[str, Any],
) -> None:
    """Render the result count and farmer identity banner.

    Args:
        count: Total schemes displayed.
        eligible_count: Number with an ELIGIBLE verdict.
        partial_count: Number with a PARTIAL verdict.
        not_eligible_count: Number with a NOT_ELIGIBLE verdict.
        farmer_profile: Profile associated with the run.

    Returns:
        None.
    """

    st.markdown(
        f"""<div class="result-summary">
            <h2>🎉 Found {count} Schemes For You!</h2>
            <p class="result-counts">
                <span class="count-eligible">{eligible_count} Eligible</span>
                <span>·</span>
                <span class="count-partial">{partial_count} Partial</span>
                <span>·</span>
                <span class="count-ineligible">{not_eligible_count} Not Eligible</span>
            </p>
            <p class="result-owner">
                Results for: {safe_html(farmer_profile.get('name', 'Farmer'))}
                &nbsp;|&nbsp; {safe_html(farmer_profile.get('state', ''))}
            </p>
        </div>""",
        unsafe_allow_html=True,
    )


def render_agent_log(result: dict[str, Any]) -> None:
    """Render the auditable agent decision log.

    Args:
        result: Final agent state containing agent_log.

    Returns:
        None.
    """

    with st.expander("🔍 Agent Decision Log"):
        st.code(
            json.dumps(result.get("agent_log", []), indent=2, ensure_ascii=False),
            language="json",
        )


def render_results(result: dict[str, Any], farmer_profile: dict[str, Any]) -> None:
    """Render filtered results, application guidance, and report download.

    Args:
        result: Final AgentState returned by LangGraph.
        farmer_profile: Farmer profile used for the current result.

    Returns:
        None.
    """

    farmer_state = str(farmer_profile.get("state", ""))
    if not result.get("is_valid_query"):
        st.error(
            result.get("guardrail_message")
            or "Please ask a farming or farmer-scheme related question."
        )
        render_agent_log(result)
        return

    if result.get("error"):
        st.error(str(result["error"]))
        render_agent_log(result)
        return

    matched_schemes = list(result.get("matched_schemes", []))
    eligibility_results = list(result.get("eligibility_results", []))
    display_results = [
        item
        for item in eligibility_results
        if should_display_scheme_for_state(item, farmer_state)
    ]

    if not matched_schemes:
        st.warning(result.get("final_response") or "No schemes matched this profile.")
        render_agent_log(result)
        return

    if not display_results:
        st.warning(
            "No scheme cards matched the selected state after state-specific filtering. "
            "Please verify the selected state and try again."
        )
        render_agent_log(result)
        return

    eligible_results = [
        item for item in display_results if str(item.get("verdict", "")).upper() == "ELIGIBLE"
    ]
    partial_results = [
        item for item in display_results if str(item.get("verdict", "")).upper() == "PARTIAL"
    ]
    not_eligible_results = [
        item
        for item in display_results
        if str(item.get("verdict", "")).upper() == "NOT_ELIGIBLE"
    ]

    render_result_summary(
        len(display_results),
        len(eligible_results),
        len(partial_results),
        len(not_eligible_results),
        farmer_profile,
    )

    all_tab, eligible_tab, partial_tab, apply_tab = st.tabs(
        ["All Schemes", "✅ Eligible Only", "⚠️ Partial", "📖 How to Apply"]
    )
    with all_tab:
        render_result_collection(display_results, "No matched schemes are available.")
    with eligible_tab:
        render_result_collection(
            eligible_results,
            "No schemes received a fully eligible verdict for this profile.",
        )
    with partial_tab:
        render_result_collection(
            partial_results,
            "No schemes require partial or conditional verification.",
        )
    with apply_tab:
        render_application_guide(eligible_results)

    farmer_name = str(farmer_profile.get("name", "Farmer")).strip() or "Farmer"
    st.download_button(
        label="📥 Download My Scheme Report (TXT)",
        data=generate_report_text(display_results, farmer_profile),
        file_name=f"SaarthiGrid_{farmer_name}_Report.txt",
        mime="text/plain",
        use_container_width=True,
        key="scheme_report_download",
    )
    render_agent_log(result)


def render_find_my_schemes_tab() -> None:
    """Render the primary farmer scheme search experience.

    Args:
        None.

    Returns:
        None.
    """

    if "last_result" in st.session_state and "results" not in st.session_state:
        st.session_state["results"] = st.session_state["last_result"]

    render_hero()
    render_stats_bar()

    if "results" not in st.session_state:
        render_get_started_guide()
        render_scheme_preview()

    st.markdown('<div class="workspace-heading">Start Your Scheme Search</div>', unsafe_allow_html=True)
    form_column, result_column = st.columns([0.38, 0.62], gap="large")
    with form_column:
        submitted, farmer_profile, query = render_profile_form()

    with result_column:
        if submitted:
            if (
                not farmer_profile["name"]
                or not farmer_profile["district"]
                or not farmer_profile["crop_type"]
            ):
                st.session_state.pop("last_result", None)
                st.session_state.pop("results", None)
                st.error("Please enter name, district, and primary crop before searching.")
                return
            with st.spinner("Consulting scheme database..."):
                try:
                    run_agent(farmer_profile, query)
                except Exception as exc:
                    st.session_state.pop("last_result", None)
                    st.session_state.pop("results", None)
                    st.error(f"The agent could not complete this run: {exc}")
                    return

        result = st.session_state.get("last_result")
        profile = st.session_state.get("last_profile")
        if result and profile:
            render_results(result, profile)
        else:
            st.markdown(
                """<div class="empty-results">
                    <div class="empty-results-icon">🌾</div>
                    <h3>Your matched schemes will appear here</h3>
                    <p>Complete the farm profile and let SaarthiGrid build your personalized action plan.</p>
                </div>""",
                unsafe_allow_html=True,
            )


def render_about_tab() -> None:
    """Render project information, team details, and data sources.

    Args:
        None.

    Returns:
        None.
    """

    st.title("About SaarthiGrid AI")
    st.write(
        "SaarthiGrid AI is a HIMSHIKHAR 2026 AAI Capstone project that helps farmers "
        "navigate central and Himachal Pradesh subsidy, insurance, credit, irrigation, "
        "horticulture, livestock, and advisory schemes."
    )

    overview_column, team_column = st.columns(2)
    with overview_column:
        st.subheader("Project Snapshot")
        st.markdown(
            """
            - **Agent type:** LangGraph multi-node RAG workflow
            - **Knowledge base:** 25 government schemes
            - **Primary users:** Farmers, extension workers, rural service operators
            - **Responsible AI stance:** Advisory only; no approval guarantees
            """
        )
    with team_column:
        st.subheader("Team")
        st.markdown(
            """
            - Team [Name]
            - HIMSHIKHAR 2026 | AAI Capstone
            - Built for farmer-first public-service navigation
            """
        )

    st.subheader("Data Sources")
    st.markdown(
        """
        - [PM-KISAN](https://pmkisan.gov.in/)
        - [PMFBY](https://pmfby.gov.in/)
        - [Agriculture Infrastructure Fund](https://agriinfra.dac.gov.in/)
        - [National Food Security Mission](https://www.nfsm.gov.in/)
        - [HP Agriculture Department Schemes](https://agriculture.hp.gov.in/en/our-scheme/)
        - [HP eUdyan Horticulture Services](https://eudyan.hp.gov.in/Department/Portal/CitizenServices.aspx)
        - [HP Animal Husbandry DBT](https://hpahdbt.hp.gov.in/)
        """
    )

    st.info(
        "SaarthiGrid AI narrows the search space and prepares farmers for official verification. "
        "Final eligibility remains with the relevant department, bank, or scheme authority."
    )


def render_footer() -> None:
    """Render the always-visible project footer.

    Args:
        None.

    Returns:
        None.
    """

    st.markdown("---")
    st.markdown(
        """<footer class="saarthi-footer">
            <div>
                <div class="footer-heading footer-brand">🌾 SaarthiGrid AI</div>
                <p>HIMSHIKHAR 2026 | AAI Capstone</p>
                <p>IIT Mandi × Masai</p>
            </div>
            <div>
                <div class="footer-heading">📊 Data Sources</div>
                <p>data.gov.in · pmkisan.gov.in</p>
                <p>agriculture.hp.gov.in · pmfby.gov.in</p>
            </div>
            <div>
                <div class="footer-heading">⚠️ Disclaimer</div>
                <p>This tool provides guidance only. Eligibility decisions are made by official government bodies.</p>
            </div>
        </footer>""",
        unsafe_allow_html=True,
    )


def render_global_styles() -> None:
    """Inject the local dark-mode visual system for the Streamlit app.

    Args:
        None.

    Returns:
        None.
    """

    st.markdown(
        """<style>
        .main .block-container {
            max-width: 1440px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        @keyframes seedPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .saarthi-hero {
            display: flex;
            align-items: center;
            width: 100%;
            box-sizing: border-box;
            padding: 40px;
            margin-bottom: 18px;
            background: linear-gradient(110deg, #0a3d0a 0%, #132b18 48%, #0e1117 100%);
            border-bottom: 2px solid #00ff88;
            border-radius: 10px 10px 4px 4px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
            overflow: hidden;
        }

        .saarthi-hero-copy {
            width: 70%;
        }

        .saarthi-hero h1 {
            margin: 0;
            color: #ffffff;
            font-size: 36px;
            line-height: 1.2;
            letter-spacing: 0;
        }

        .saarthi-hero h3 {
            margin: 10px 0 8px;
            color: #00ff88;
            font-size: 18px;
            line-height: 1.35;
            letter-spacing: 0;
        }

        .saarthi-hero p {
            margin: 0 0 18px;
            color: #cccccc;
            font-size: 14px;
            line-height: 1.55;
        }

        .hero-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .hero-badges span {
            display: inline-block;
            padding: 4px 12px;
            margin-right: 0;
            color: #00ff88;
            background: #1a2e1a;
            border: 1px solid #00ff88;
            border-radius: 20px;
            font-size: 12px;
            line-height: 1.5;
            white-space: nowrap;
        }

        .saarthi-hero-visual {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30%;
            min-height: 110px;
            font-size: 80px;
            line-height: 1;
            animation: seedPulse 2s ease-in-out infinite;
            transform-origin: center;
        }

        .metric-card {
            min-height: 142px;
            box-sizing: border-box;
            padding: 20px;
            text-align: center;
            background: #1a1f2e;
            border: 1px solid #2a3f2a;
            border-radius: 10px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.14);
        }

        .metric-icon {
            margin-bottom: 8px;
            font-size: 24px;
            line-height: 1;
        }

        .metric-number {
            color: #00ff88;
            font-size: 28px;
            font-weight: 800;
            line-height: 1.15;
        }

        .metric-label {
            margin-top: 7px;
            color: #888888;
            font-size: 12px;
            line-height: 1.35;
        }

        .step-card {
            height: 180px;
            box-sizing: border-box;
            padding: 18px 20px;
            text-align: center;
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
        }

        .step-top {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            min-height: 39px;
        }

        .step-number {
            color: #00ff88;
            font-size: 32px;
            line-height: 1;
        }

        .step-icon {
            font-size: 24px;
            line-height: 1;
        }

        .step-title {
            margin-top: 8px;
            color: #ffffff;
            font-size: 16px;
            font-weight: 700;
            line-height: 1.25;
        }

        .step-text {
            margin-top: 9px;
            color: #9ca3af;
            font-size: 13px;
            line-height: 1.42;
        }

        .scheme-list {
            display: grid;
            gap: 9px;
            padding: 4px 0;
        }

        .scheme-list-row {
            display: grid;
            grid-template-columns: 22px 1fr;
            align-items: start;
            color: #d1d5db;
            font-size: 13px;
            line-height: 1.45;
        }

        .workspace-heading {
            margin: 26px 0 12px;
            color: #f8fafc;
            font-size: 22px;
            font-weight: 750;
        }

        div[data-testid="stForm"] {
            padding: 22px;
            background: #111827;
            border: 1px solid #263244;
            border-radius: 10px;
        }

        div[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
            color: #052e16;
            background: #00ff88;
            border-color: #00ff88;
            font-weight: 800;
        }

        .empty-results {
            min-height: 300px;
            box-sizing: border-box;
            padding: 52px 28px;
            text-align: center;
            background: #0f172a;
            border: 1px dashed #334155;
            border-radius: 10px;
        }

        .empty-results-icon {
            font-size: 44px;
        }

        .empty-results h3 {
            margin: 14px 0 8px;
            color: #f8fafc;
            font-size: 20px;
            letter-spacing: 0;
        }

        .empty-results p {
            max-width: 480px;
            margin: 0 auto;
            color: #94a3b8;
            font-size: 14px;
            line-height: 1.55;
        }

        .result-summary {
            box-sizing: border-box;
            padding: 26px 22px;
            margin-bottom: 18px;
            text-align: center;
            background: linear-gradient(115deg, #0a3d0a 0%, #142a18 52%, #0e1117 100%);
            border: 1px solid #1d6b3a;
            border-bottom: 2px solid #00ff88;
            border-radius: 10px;
        }

        .result-summary h2 {
            margin: 0;
            color: #ffffff;
            font-size: 27px;
            line-height: 1.25;
            letter-spacing: 0;
        }

        .result-counts {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
            margin: 10px 0 6px;
            color: #9ca3af;
            font-size: 14px;
        }

        .count-eligible { color: #10b981; font-weight: 700; }
        .count-partial { color: #f59e0b; font-weight: 700; }
        .count-ineligible { color: #ef4444; font-weight: 700; }

        .result-owner {
            margin: 0;
            color: #cbd5e1;
            font-size: 12px;
        }

        div[data-testid="stTabs"] button {
            font-weight: 700;
            letter-spacing: 0;
        }

        div[data-testid="stExpander"] {
            margin-bottom: 10px;
            background: #111827;
            border-color: #293548;
            border-radius: 8px;
        }

        .scheme-card-body {
            padding: 2px 4px 8px;
        }

        .scheme-card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 14px;
            padding: 4px 0 15px;
            border-bottom: 1px solid #263244;
        }

        .scheme-card-name {
            color: #f8fafc;
            font-size: 17px;
            font-weight: 750;
            line-height: 1.4;
        }

        .verdict-pill {
            flex: 0 0 auto;
            padding: 5px 10px;
            border: 1px solid currentColor;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 800;
            line-height: 1.2;
        }

        .scheme-card-section {
            padding: 15px 0 2px;
        }

        .scheme-card-label {
            color: #f8fafc;
            font-size: 14px;
            font-weight: 750;
        }

        .scheme-card-section p,
        .scheme-card-section li {
            color: #cbd5e1;
            font-size: 13px;
            line-height: 1.58;
        }

        .scheme-card-section p {
            margin: 7px 0 0;
        }

        .scheme-card-section ul {
            margin: 8px 0 0;
            padding-left: 21px;
        }

        .eligibility-note {
            margin-top: 12px;
            padding: 13px 14px;
            background: #0f172a;
            border-left: 3px solid #64748b;
            border-radius: 4px;
        }

        .next-step-section {
            margin-top: 10px;
            padding: 14px;
            background: #092814;
            border-left: 3px solid #00ff88;
            border-radius: 4px;
        }

        .scheme-card-action {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 16px;
            color: #94a3b8;
            font-size: 13px;
        }

        .scheme-apply {
            display: inline-block;
            padding: 8px 14px;
            color: #052e16 !important;
            background: #00ff88;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 800;
            text-decoration: none !important;
        }

        .scheme-apply:hover {
            background: #6dffae;
        }

        .scheme-office span {
            color: #e2e8f0;
            font-weight: 700;
        }

        .apply-guide-intro {
            margin: 4px 0 12px;
            color: #94a3b8;
            font-size: 13px;
        }

        .apply-guide {
            margin: 0;
            padding-left: 32px;
        }

        .apply-guide li {
            margin-bottom: 12px;
            padding: 15px 18px;
            color: #00ff88;
            background: #111827;
            border: 1px solid #263244;
            border-radius: 8px;
        }

        .apply-guide-name {
            color: #f8fafc;
            font-size: 15px;
            font-weight: 750;
        }

        .apply-guide p {
            margin: 7px 0;
            color: #cbd5e1;
            font-size: 13px;
            line-height: 1.55;
        }

        .apply-guide-link a,
        .apply-guide-link span {
            color: #00ff88;
            font-size: 12px;
            font-weight: 700;
        }

        div[data-testid="stDownloadButton"] button {
            color: #052e16;
            background: #00ff88;
            border-color: #00ff88;
            font-weight: 800;
        }

        .saarthi-footer {
            display: grid;
            grid-template-columns: 1fr 1fr 1.2fr;
            gap: 30px;
            box-sizing: border-box;
            padding: 20px;
            background: #0a0a0a;
            border-top: 1px solid #1f2937;
            border-radius: 6px;
            color: #6b7280;
            font-size: 12px;
            line-height: 1.55;
        }

        .footer-heading {
            margin-bottom: 7px;
            color: #d1d5db;
            font-size: 13px;
            font-weight: 750;
        }

        .footer-brand {
            color: #00ff88;
        }

        .saarthi-footer p {
            margin: 2px 0;
        }

        @media (max-width: 760px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .saarthi-hero {
                padding: 26px 22px;
            }

            .saarthi-hero-copy {
                width: 100%;
            }

            .saarthi-hero-visual {
                display: none;
            }

            .saarthi-hero h1 {
                font-size: 30px;
            }

            .hero-badges span {
                white-space: normal;
            }

            .step-card {
                height: auto;
                min-height: 180px;
            }

            .scheme-card-head {
                flex-direction: column;
            }

            .saarthi-footer {
                grid-template-columns: 1fr;
                gap: 18px;
            }
        }
        </style>""",
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the SaarthiGrid Streamlit application.

    Args:
        None.

    Returns:
        None.
    """

    st.set_page_config(
        page_title="SaarthiGrid AI 🌾",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    render_global_styles()

    tabs = st.tabs(["🌾 Find My Schemes", "⚙️ How It Works", "📊 About"])
    with tabs[0]:
        render_find_my_schemes_tab()
    with tabs[1]:
        render_how_it_works()
    with tabs[2]:
        render_about_tab()

    render_footer()


if __name__ == "__main__":
    main()
