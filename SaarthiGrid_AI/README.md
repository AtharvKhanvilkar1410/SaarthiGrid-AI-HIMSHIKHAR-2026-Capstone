# SaarthiGrid AI 🌾
### Farmer Subsidy and Advisory Navigation Agent

SaarthiGrid AI is a production-quality Agentic AI project. It helps farmers discover Indian government subsidy and advisory schemes by combining a structured scheme knowledge base, deterministic eligibility filtering, LangGraph orchestration, and farmer-friendly LLM explanations. The project focuses on a real use case: a farmer often knows their crop, land size, district, caste category, income, and existing registrations, but does not know which central or state schemes apply or where to begin.

The first release includes 25 real schemes: 15 central government schemes and 10 Himachal Pradesh schemes across income support, crop insurance, pension, credit, soil health, irrigation, market access, infrastructure, organic farming, horticulture, mechanization, seeds, livestock, and mushroom cultivation. The system is intentionally conservative. It does not approve applications and does not promise benefits. Instead, it says a farmer may qualify, explains the reason, lists documents, and points to the official portal or department office.

## 1. Project Overview

The project addresses the information gap between public policy and last-mile farmer access. Indian agriculture has many support schemes, but eligibility can depend on crop, state, district targets, land records, category, income, bank sanction, and annual action plans. Generic search results and static lists do not personalize this information. A plain chatbot can be risky because it may hallucinate scheme rules or overstate approval.

SaarthiGrid AI solves this by using a structured Retrieval-Augmented Generation approach. The retrieval layer is `data/scheme_rules.csv`, a reviewed CSV with explicit eligibility columns. The agent first filters schemes deterministically, then uses an LLM, when configured, to explain eligibility in simple English. If no OpenAI key is configured, deterministic fallback logic still produces runnable test and demo behavior.

## 2. Live Demo

[Insert screenshot GIF of Streamlit demo here]

The Streamlit app provides a sidebar farmer profile form and a main results area. Each matched scheme appears in an expander with a verdict, benefit summary, eligibility reason, documents, next step, and official portal button. The bottom decision log shows the exact agent steps.

## 3. Architecture

```
Farmer Profile + Query
        |
        v
  [Guardrail Node] -- blocked --> END
        |
        v
 [Profile Parser]
        |
        v
 [CSV Scheme Matcher] <---- data/scheme_rules.csv
        |
        v
 [Eligibility Checker] <---- OpenAI LLM or fallback logic
        |
        v
 [Response Generator] <---- output guardrails
        |
        v
 [Logger Node] ----> logs/agent_log.json
```

## 4. Tech Stack

| Component | Technology | Why |
|---|---|---|
| Agent orchestration | LangGraph | Explicit state transitions, conditional routing, and testable nodes |
| Prompt management | LangChain PromptTemplate | Centralized prompts with clear input variables |
| LLM integration | langchain-openai | Production-ready OpenAI chat model integration |
| Retrieval/data | pandas + CSV | Auditable, deterministic scheme filtering |
| UI | Streamlit | Fast interactive prototype with forms, expanders, and JSON logs |
| Tests | pytest | Repeatable validation of valid profiles and guardrail behavior |
| Configuration | python-dotenv | Local `.env` support without hardcoding secrets |

## 5. Quickstart

1. Clone or open the project folder:

```bash
cd SaarthiGrid_AI
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run the Streamlit app:

```bash
streamlit run app/app.py
```

For LLM-powered explanations, copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Without a key, the project still runs using deterministic fallback explanations.

## 6. How to Use

[Insert screenshot of sidebar form here]

1. Enter the farmer name, state, district, land size, ownership, crop, caste category, annual income, and existing registrations.
2. Optionally describe the need, such as irrigation support, crop insurance, equipment subsidy, horticulture development, or post-harvest infrastructure.
3. Click **Find My Schemes**.
4. Review the result cards. Green means `ELIGIBLE`, yellow means `PARTIAL`, and red means `NOT_ELIGIBLE`.
5. Open the decision log to see how the agent reached the result.

## 7. Adding New Schemes

To add a scheme, edit `data/scheme_rules.csv` and add one complete row with these columns:

```text
scheme_id, scheme_name, launched_by, target_farmers, min_land_acres,
max_land_acres, eligible_crops, eligible_states, eligible_castes,
max_annual_income, benefit_summary, benefit_amount, documents_required,
how_to_apply, application_portal, scheme_category
```

Use `all` for crops, states, or castes when the scheme has no restriction. Use `999999999` when there is no income ceiling. Keep values factual and source-backed. After editing, run the tests to ensure filtering still works.

## 8. Project Structure

```text
SaarthiGrid_AI/
├── app/
│   └── app.py                  # Streamlit UI
├── src/
│   ├── agent.py                # LangGraph assembly
│   ├── nodes.py                # Node functions
│   ├── state.py                # AgentState TypedDict
│   ├── retriever.py            # CSV loading and filtering
│   ├── guardrails.py           # Input/output safety checks
│   └── prompts.py              # LangChain prompt templates
├── data/
│   ├── scheme_rules.csv        # 25-scheme knowledge base
│   └── farm_profile.csv        # Sample profiles
├── docs/
│   ├── project_report.md       # Professional project report
│   └── architecture.md         # Detailed architecture reference
├── logs/
│   └── .gitkeep                # Keeps log directory in version control
├── tests/
│   └── test_cases.py           # Pytest coverage
├── presentation/
│   └── slide_content.md        # 10-slide content and notes
├── requirements.txt
├── .env.example
└── README.md
```

## 9. Test Cases

| Test | Farmer | Scenario | Expected |
|---|---|---|---|
| 1 | Ramesh Kumar | HP, Mandi, wheat, SC, 1.5 acres | Valid query and at least 2 schemes |
| 2 | Suresh Verma | HP, Shimla, apple, General, 3 acres | Valid query and horticulture-related matches |
| 3 | Gurpreet Singh | Punjab, Ludhiana, rice, OBC, leased land | Valid query and central scheme matches |
| 4 | Birsa Munda | HP, Kinnaur, maize, ST, 2 acres | Valid query and seed/equipment support matches |
| 5 | Anita Devi | Maharashtra onion profile with IPL query | Guardrail blocks and returns no schemes |

Run tests with:

```bash
pytest -q
```

## 10. Responsible AI Notes

SaarthiGrid AI is a navigation assistant, not a government approval system. It avoids false certainty by using deterministic rule filters before generation and by validating output language. The response generator hedges claims such as "may qualify" because final approval may depend on official verification, district targets, crop notification, bank appraisal, and document checks. The project does not store Aadhaar numbers, bank account numbers, certificates, or uploaded documents.

## 11. Limitations

The current database is curated manually. Subsidy percentages, application windows, and state annual action plans can change. The first version is English-only, which limits accessibility. The app does not integrate live land records, CSC systems, bank APIs, or department application status. Some schemes, such as PMFBY and AIF, require external conditions that cannot be fully determined from a short farm profile.

## 12. Future Roadmap

- Hindi, Punjabi, Marathi, and local dialect interfaces.
- Voice input for low-literacy or mobile-first users.
- WhatsApp integration for rural service delivery.
- Official PDF and circular ingestion with citation-level RAG.
- District officer dashboard for scheme targets and document gaps.
- Real-time scheme update workflow with reviewer approval.

## 13. Team

Team SaarthiGrid AI
Roles: AI engineering, data curation, documentation, testing, and presentation.
