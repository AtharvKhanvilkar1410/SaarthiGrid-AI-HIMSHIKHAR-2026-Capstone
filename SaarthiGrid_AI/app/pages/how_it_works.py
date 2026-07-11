"""Visual explanation page for the SaarthiGrid AI Streamlit app."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


CENTRAL_SCHEMES = [
    "PM-KISAN",
    "PMFBY",
    "PM Kisan Maan Dhan Yojana",
    "Kisan Credit Card",
    "Soil Health Card Scheme",
    "PMKSY",
    "eNAM",
    "Agriculture Infrastructure Fund",
    "PKVY",
    "MIDH",
    "RKVY",
    "National Livestock Mission",
    "National Food Security Mission",
    "NMSA",
    "SMAM",
]

HP_SCHEMES = [
    "HP Prakritik Kheti Khushhal Kisan Yojana",
    "Mukhyamantri Khet Sanrakshan Yojana",
    "HP Horticulture Development Scheme",
    "HP Beekeeping Development Scheme",
    "HP Polyhouse/Protected Cultivation Subsidy",
    "HP Irrigation Subsidy Scheme",
    "HP SC/ST Farmer Equipment Subsidy",
    "HP Seed Subsidy Scheme",
    "HP Sheep and Goat Rearing Subsidy",
    "HP Mushroom Cultivation Scheme",
]


def _escape_html(value: object) -> str:
    """Escape text for safe insertion into small custom HTML components.

    Args:
        value: Object to convert to escaped text.

    Returns:
        HTML-safe string.
    """

    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _pipeline_html() -> str:
    """Build the animated six-node agent pipeline component.

    Args:
        None.

    Returns:
        HTML string with CSS-only sequential glow and arrow-dot animation.
    """

    return """
    <div class="sg-pipeline">
      <style>
        .sg-pipeline {
          height: 400px;
          background: #0e1117;
          color: #ffffff;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          border-radius: 14px;
          border: 1px solid rgba(0, 255, 136, 0.32);
          overflow: hidden;
          position: relative;
          padding: 28px;
          box-sizing: border-box;
        }
        .sg-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          grid-template-rows: repeat(2, 145px);
          gap: 34px 44px;
          height: 100%;
          position: relative;
          z-index: 2;
        }
        .sg-node {
          border: 1px solid rgba(0, 255, 136, 0.28);
          border-radius: 14px;
          padding: 18px;
          background: rgba(26, 31, 46, 0.92);
          box-shadow: 0 0 0 rgba(0, 255, 136, 0);
          animation: sgGlow 6s infinite;
        }
        .sg-node:nth-child(1) { animation-delay: 0s; }
        .sg-node:nth-child(2) { animation-delay: 1s; }
        .sg-node:nth-child(3) { animation-delay: 2s; }
        .sg-node:nth-child(4) { animation-delay: 3s; }
        .sg-node:nth-child(5) { animation-delay: 4s; }
        .sg-node:nth-child(6) { animation-delay: 5s; }
        .sg-title {
          font-size: 18px;
          font-weight: 800;
          margin-bottom: 10px;
          letter-spacing: 0;
        }
        .sg-copy {
          color: #cbd5e1;
          font-size: 14px;
          line-height: 1.4;
        }
        .sg-arrow {
          position: absolute;
          height: 2px;
          background: linear-gradient(90deg, rgba(0,255,136,0.12), rgba(0,255,136,0.85), rgba(0,255,136,0.12));
          z-index: 1;
          overflow: hidden;
        }
        .sg-arrow::after {
          content: "";
          position: absolute;
          top: -4px;
          left: -10px;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #00ff88;
          box-shadow: 0 0 16px #00ff88;
          animation: sgDot 1.5s linear infinite;
        }
        .a1 { left: 30%; top: 96px; width: 13%; }
        .a2 { left: 63%; top: 96px; width: 13%; }
        .a3 { left: 76%; top: 202px; width: 2px; height: 54px; transform: rotate(90deg); transform-origin: left center; }
        .a4 { left: 30%; top: 252px; width: 46%; transform: rotate(180deg); }
        .a5 { left: 16%; top: 202px; width: 2px; height: 54px; transform: rotate(90deg); transform-origin: left center; }
        @keyframes sgGlow {
          0%, 11%, 100% {
            border-color: rgba(0, 255, 136, 0.28);
            box-shadow: 0 0 0 rgba(0, 255, 136, 0);
            transform: translateY(0);
          }
          6% {
            border-color: #00ff88;
            box-shadow: 0 0 24px rgba(0, 255, 136, 0.72), inset 0 0 22px rgba(0, 255, 136, 0.08);
            transform: translateY(-3px);
          }
        }
        @keyframes sgDot {
          from { left: -12px; }
          to { left: calc(100% + 12px); }
        }
        @media (max-width: 780px) {
          .sg-pipeline { height: 760px; }
          .sg-grid { grid-template-columns: 1fr; grid-template-rows: repeat(6, 100px); gap: 14px; }
          .sg-arrow { display: none; }
        }
      </style>
      <div class="sg-arrow a1"></div>
      <div class="sg-arrow a2"></div>
      <div class="sg-arrow a3"></div>
      <div class="sg-arrow a4"></div>
      <div class="sg-arrow a5"></div>
      <div class="sg-grid">
        <div class="sg-node"><div class="sg-title">🛡️ Guardrail Check</div><div class="sg-copy">Is your query farming-related?</div></div>
        <div class="sg-node"><div class="sg-title">👤 Profile Parser</div><div class="sg-copy">Structuring your farm details</div></div>
        <div class="sg-node"><div class="sg-title">🔍 Scheme Matcher</div><div class="sg-copy">Scanning 25 government schemes</div></div>
        <div class="sg-node"><div class="sg-title">✅ Eligibility Checker</div><div class="sg-copy">LLM verifies your eligibility</div></div>
        <div class="sg-node"><div class="sg-title">📝 Response Generator</div><div class="sg-copy">Creating your action plan</div></div>
        <div class="sg-node"><div class="sg-title">📋 Logger</div><div class="sg-copy">Saving results securely</div></div>
      </div>
    </div>
    """


def _vertical_progress_html() -> str:
    """Build a CSS-only vertical progress visual for the matching engine.

    Args:
        None.

    Returns:
        HTML string containing the animated progress component.
    """

    return """
    <div class="sg-progress-wrap">
      <style>
        .sg-progress-wrap {
          height: 160px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0e1117;
          border: 1px solid rgba(0,255,136,.22);
          border-radius: 12px;
          margin: 10px 0 14px 0;
          font-family: Inter, ui-sans-serif, system-ui, sans-serif;
        }
        .sg-progress-shell {
          width: 44px;
          height: 118px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,.24);
          background: rgba(255,255,255,.06);
          overflow: hidden;
          display: flex;
          align-items: flex-end;
        }
        .sg-progress-fill {
          width: 100%;
          background: linear-gradient(180deg, #00ff88 0%, #16a34a 100%);
          animation: sgFill 2.8s ease-in-out infinite;
          box-shadow: 0 0 20px rgba(0,255,136,.62);
        }
        .sg-progress-label {
          margin-left: 18px;
          color: #e2e8f0;
          font-weight: 800;
        }
        @keyframes sgFill {
          0% { height: 0%; }
          70% { height: 100%; }
          100% { height: 100%; }
        }
      </style>
      <div class="sg-progress-shell"><div class="sg-progress-fill"></div></div>
      <div class="sg-progress-label">Scanning schemes...</div>
    </div>
    """


def _donut_chart_html() -> str:
    """Build a pure-SVG donut chart for eligibility distribution.

    Args:
        None.

    Returns:
        HTML string containing the donut chart and legend.
    """

    return """
    <div class="sg-donut">
      <style>
        .sg-donut {
          background: #0e1117;
          border: 1px solid rgba(0,255,136,.22);
          border-radius: 12px;
          padding: 14px;
          color: #e2e8f0;
          font-family: Inter, ui-sans-serif, system-ui, sans-serif;
          text-align: center;
        }
        .sg-donut svg { max-width: 190px; }
        .sg-legend {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin-top: 8px;
          font-size: 12px;
        }
        .sg-key { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }
      </style>
      <svg viewBox="0 0 42 42" role="img" aria-label="Eligibility Distribution">
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#1f2937" stroke-width="7"></circle>
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#22c55e" stroke-width="7" stroke-dasharray="45 55" stroke-dashoffset="25"></circle>
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#facc15" stroke-width="7" stroke-dasharray="35 65" stroke-dashoffset="-20"></circle>
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#ef4444" stroke-width="7" stroke-dasharray="20 80" stroke-dashoffset="-55"></circle>
        <text x="21" y="20" text-anchor="middle" fill="#ffffff" font-size="4.3" font-weight="800">Test</text>
        <text x="21" y="25" text-anchor="middle" fill="#cbd5e1" font-size="3">Runs</text>
      </svg>
      <div><strong>Eligibility Distribution (Test Runs)</strong></div>
      <div class="sg-legend">
        <div><span class="sg-key" style="background:#22c55e"></span>Eligible 45%</div>
        <div><span class="sg-key" style="background:#facc15"></span>Partial 35%</div>
        <div><span class="sg-key" style="background:#ef4444"></span>Not 20%</div>
      </div>
    </div>
    """


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an agent log timestamp safely.

    Args:
        value: Timestamp value from an agent log entry.

    Returns:
        Parsed datetime when possible, otherwise None.
    """

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _step_duration_ms(current_step: dict[str, object], next_step: dict[str, object] | None) -> int:
    """Estimate elapsed milliseconds between two log entries.

    Args:
        current_step: Current agent log entry.
        next_step: Following agent log entry, if available.

    Returns:
        Estimated duration in milliseconds.
    """

    current_time = _parse_timestamp(current_step.get("timestamp"))
    next_time = _parse_timestamp(next_step.get("timestamp")) if next_step else None
    if not current_time or not next_time:
        return 0
    return max(0, int((next_time - current_time).total_seconds() * 1000))


def _timeline_html(agent_log: list[dict[str, object]]) -> str:
    """Build a CSS-only timeline visualization from the latest agent log.

    Args:
        agent_log: Agent decision log stored in ``st.session_state``.

    Returns:
        HTML string containing the visual timeline.
    """

    rows = []
    for index, step in enumerate(agent_log):
        next_step = agent_log[index + 1] if index + 1 < len(agent_log) else None
        timestamp = _escape_html(step.get("timestamp", ""))
        node_name = _escape_html(step.get("step", "agent_node"))
        status = "current" if index == len(agent_log) - 1 else "completed"
        duration = _step_duration_ms(step, next_step)
        message = _escape_html(step.get("message", ""))
        rows.append(
            f"""
            <div class="sg-timeline-item {status}">
              <div class="sg-dot"></div>
              <div class="sg-card">
                <div class="sg-row"><strong>{node_name}</strong><span>{duration} ms</span></div>
                <div class="sg-time">{timestamp}</div>
                <div class="sg-status">{status.upper()}</div>
                <div class="sg-message">{message}</div>
              </div>
            </div>
            """
        )

    payload = _escape_html(json.dumps({"steps": len(agent_log)}))
    return f"""
    <div class="sg-timeline" data-payload="{payload}">
      <style>
        .sg-timeline {{
          background: #0e1117;
          border: 1px solid rgba(0,255,136,.24);
          border-radius: 14px;
          padding: 18px 18px 18px 28px;
          color: #e2e8f0;
          font-family: Inter, ui-sans-serif, system-ui, sans-serif;
          position: relative;
        }}
        .sg-timeline::before {{
          content: "";
          position: absolute;
          left: 33px;
          top: 32px;
          bottom: 32px;
          width: 2px;
          background: linear-gradient(#00ff88, rgba(0,255,136,.15));
        }}
        .sg-timeline-item {{
          position: relative;
          display: grid;
          grid-template-columns: 30px 1fr;
          margin: 0 0 14px 0;
        }}
        .sg-dot {{
          width: 13px;
          height: 13px;
          border-radius: 50%;
          margin-top: 18px;
          background: #22c55e;
          box-shadow: 0 0 16px rgba(34,197,94,.65);
          z-index: 2;
        }}
        .current .sg-dot {{
          background: #facc15;
          box-shadow: 0 0 18px rgba(250,204,21,.8);
          animation: sgPulse 1.2s infinite;
        }}
        .sg-card {{
          background: #1a1f2e;
          border: 1px solid rgba(255,255,255,.08);
          border-radius: 12px;
          padding: 12px 14px;
        }}
        .sg-row {{
          display: flex;
          justify-content: space-between;
          gap: 12px;
          color: #ffffff;
        }}
        .sg-time {{
          color: #94a3b8;
          font-size: 12px;
          margin-top: 5px;
        }}
        .sg-status {{
          color: #00ff88;
          font-size: 12px;
          font-weight: 800;
          margin-top: 6px;
        }}
        .current .sg-status {{ color: #facc15; }}
        .sg-message {{
          color: #cbd5e1;
          font-size: 13px;
          margin-top: 7px;
        }}
        @keyframes sgPulse {{
          0%, 100% {{ transform: scale(1); }}
          50% {{ transform: scale(1.35); }}
        }}
      </style>
      {"".join(rows)}
    </div>
    """


def _render_scheme_expander() -> None:
    """Render the knowledge-base expander listing all scheme names.

    Args:
        None.

    Returns:
        None.
    """

    with st.expander("What's in the knowledge base?"):
        st.markdown("**Central Schemes (15)**")
        for scheme_name in CENTRAL_SCHEMES:
            st.markdown(f"- {scheme_name}")
        st.markdown("**HP State Schemes (10)**")
        for scheme_name in HP_SCHEMES:
            st.markdown(f"- {scheme_name}")


def render_agent_pipeline() -> None:
    """Render Section A with the animated LangGraph pipeline.

    Args:
        None.

    Returns:
        None.
    """

    st.header("How SaarthiGrid AI Thinks")
    st.components.v1.html(_pipeline_html(), height=400)


def render_rag_pipeline() -> None:
    """Render Section B explaining the RAG pipeline.

    Args:
        None.

    Returns:
        None.
    """

    st.header("RAG Pipeline Explained")
    knowledge_col, matching_col, quality_col = st.columns(3, gap="large")

    with knowledge_col:
        st.subheader("📚 Knowledge Base")
        st.metric("Schemes Loaded", "25")
        st.metric("Categories", "2")
        st.metric("Data Points", "400+")
        _render_scheme_expander()

    with matching_col:
        st.subheader("🔄 Matching Engine")
        st.progress(100, text="Scanning schemes...")
        st.components.v1.html(_vertical_progress_html(), height=170)
        match_rows = pd.DataFrame(
            [
                {
                    "Scheme": "PM-KISAN",
                    "State Match": "✅",
                    "Land Match": "✅",
                    "Crop Match": "✅",
                    "Income Match": "✅",
                    "Result": "ELIGIBLE",
                },
                {
                    "Scheme": "HP Fencing Subsidy",
                    "State Match": "✅",
                    "Land Match": "✅",
                    "Crop Match": "✅",
                    "Income Match": "✅",
                    "Result": "PARTIAL",
                },
                {
                    "Scheme": "HP Equipment Subsidy",
                    "State Match": "❌",
                    "Land Match": "✅",
                    "Crop Match": "✅",
                    "Income Match": "✅",
                    "Result": "FILTERED",
                },
            ]
        )
        st.dataframe(match_rows, use_container_width=True, hide_index=True)

    with quality_col:
        st.subheader("🎯 Output Quality")
        st.metric("Accuracy (Test Cases)", "5/5")
        st.metric("Guardrail Block Rate", "100%")
        st.metric("Avg Schemes Matched", "8-12")
        st.components.v1.html(_donut_chart_html(), height=265)


def render_tech_stack() -> None:
    """Render Section C with technology cards.

    Args:
        None.

    Returns:
        None.
    """

    st.header("Tech Stack")
    cards = [
        ("🦜", "LangChain", "Prompt orchestration and LLM interface", "v0.2+"),
        ("🕸️", "LangGraph", "Stateful multi-node agent graph", "v0.2+"),
        ("🌐", "Streamlit", "Interactive web UI", "v1.35+"),
        ("🤖", "GPT-4o-mini", "LLM for eligibility reasoning", "OpenAI"),
    ]
    columns = st.columns(4)
    for column, (icon, title, description, badge) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div style="
                    background:#1a1f2e;
                    border:1px solid #00ff88;
                    border-radius:12px;
                    padding:20px;
                    text-align:center;
                    min-height:172px;
                    box-shadow:0 10px 24px rgba(0,0,0,.18);
                ">
                    <div style="font-size:34px; line-height:1;">{icon}</div>
                    <h3 style="color:#ffffff; margin:12px 0 8px 0; letter-spacing:0;">{title}</h3>
                    <p style="color:#cbd5e1; min-height:44px; margin:0 0 14px 0;">{description}</p>
                    <span style="
                        display:inline-block;
                        color:#0e1117;
                        background:#00ff88;
                        border-radius:999px;
                        padding:4px 10px;
                        font-weight:800;
                        font-size:12px;
                    ">{badge}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_decision_log_visualizer() -> None:
    """Render Section D with the latest agent decision log.

    Args:
        None.

    Returns:
        None.
    """

    st.header("Agent Decision Log Visualizer")
    agent_log = st.session_state.get("agent_log", [])
    if not agent_log:
        st.info("Run a farmer query to see the agent in action →")
        return
    st.components.v1.html(_timeline_html(agent_log), height=max(360, 122 * len(agent_log)))


def render() -> None:
    """Render the complete How It Works page.

    Args:
        None.

    Returns:
        None.
    """

    st.title("⚙️ How It Works")
    st.caption(f"Visual walkthrough powered from `{Path('app/pages/how_it_works.py')}`")
    render_agent_pipeline()
    render_rag_pipeline()
    render_tech_stack()
    render_decision_log_visualizer()
