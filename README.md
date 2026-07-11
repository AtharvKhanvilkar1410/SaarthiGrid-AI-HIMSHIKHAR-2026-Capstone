# SaarthiGrid AI
### Farmer Subsidy and Advisory Navigation Agent

SaarthiGrid AI is a production-quality Agentic AI capstone project for HIMSHIKHAR 2026. It helps Indian farmers discover relevant government subsidy and advisory schemes by combining a structured scheme knowledge base, deterministic eligibility filtering, LangGraph orchestration, and farmer-friendly explanations.

Farmers often know their crop, land size, district, social category, income, and existing registrations but still struggle to determine which schemes apply, what documents are required, and where to begin. SaarthiGrid AI turns that profile into a transparent shortlist of schemes and a practical action plan without claiming to make an official eligibility decision.

## Project Deliverables

| Deliverable | Link |
|---|---|
| Narrated application demo | [Watch the MP4](https://drive.google.com/file/d/1Nzxt_I9WCIaEZeF0qClkZ-ptkzQ7Yq3A/view?usp=drivesdk) |
| Capstone presentation | [Open the PowerPoint](https://docs.google.com/presentation/d/1vf9oGh8qJ6QKxLFSLX8jVoYLtT6z8-_L/edit?usp=drivesdk) |
| Complete project ZIP | [Open the ZIP](https://drive.google.com/file/d/1VsLBTKOVSr-LzigeXULD5fo90MNj3TFz/view?usp=drivesdk) |
| Shared submission folder | [Open Google Drive](https://drive.google.com/drive/folders/1u32HnKpbgRGh0C9nzMdruUtwJ_APf5VM) |

## Project Overview

The first release contains 25 government schemes: 15 central schemes and 10 Himachal Pradesh schemes covering income support, crop insurance, pension, credit, soil health, irrigation, market access, infrastructure, natural farming, horticulture, mechanization, seeds, livestock, beekeeping, protected cultivation, and mushroom production.

The system is intentionally conservative. It does not approve applications or promise benefits. It identifies schemes that may fit the supplied profile, explains the evidence, lists likely documents, and directs the farmer to an official portal or department office for verification.

## Key Features

- Six-node LangGraph workflow with explicit state transitions.
- Structured retrieval over a reviewed 25-scheme CSV knowledge base.
- Deterministic filtering by state, land size, crop, category, and income.
- LLM-assisted eligibility explanations with deterministic offline fallbacks.
- Input guardrails for off-topic queries and output checks against false guarantees.
- Farmer-friendly scheme cards with benefits, documents, next steps, and official links.
- Downloadable personalized scheme report.
- Node-level decision log for traceability and evaluation.
- Five runnable pytest scenarios covering valid and blocked requests.

## Architecture

```text
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

LangGraph manages the workflow as an explicit state machine. A conditional edge stops invalid requests after the guardrail node. Valid farming queries continue through profile normalization, deterministic scheme retrieval, eligibility interpretation, response generation, and audit logging.

## Why Structured RAG

Fine-tuning would make frequently changing scheme rules difficult to inspect and update. SaarthiGrid AI instead stores eligibility attributes in `scheme_rules.csv`, where policy rows can be reviewed and revised without retraining a model. The model explains only schemes retrieved by structured filters, reducing hallucination risk and making each recommendation traceable to source data.

## Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| User interface | Streamlit | Fast, accessible form and results workflow |
| Agent orchestration | LangGraph | Conditional routing and testable state transitions |
| Prompt management | LangChain | Centralized, reusable prompt templates |
| LLM integration | langchain-openai | OpenAI chat model integration when configured |
| Retrieval | pandas and CSV | Deterministic, inspectable policy filtering |
| Configuration | python-dotenv | Local environment configuration without committed secrets |
| Testing | pytest | Repeatable profile and guardrail validation |

## Quickstart

1. Clone the repository and enter the project directory:

```bash
git clone https://github.com/AtharvKhanvilkar1410/SaarthiGrid-AI-HIMSHIKHAR-2026-Capstone.git
cd SaarthiGrid-AI-HIMSHIKHAR-2026-Capstone/SaarthiGrid_AI
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

3. Configure optional LLM access:

```bash
cp .env.example .env
```

On Windows, use `Copy-Item .env.example .env`. Add an `OPENAI_API_KEY` to enable model-assisted explanations. Without a key, deterministic fallback behavior keeps the application and tests runnable.

4. Start the application:

```bash
streamlit run app/app.py
```

Open `http://localhost:8501` if Streamlit does not launch a browser automatically.

## How to Use

1. Enter the farmer's state, district, land size, ownership, crop, category, income, and existing registrations.
2. Optionally describe a need such as irrigation, insurance, equipment, horticulture, credit, or post-harvest infrastructure.
3. Select **Find My Schemes**.
4. Review all matched schemes or filter the results by eligible and partial verdicts.
5. Open a scheme to inspect its benefit, reasoning, documents, exact next step, and official application channel.
6. Download the consolidated text report for offline use or discussion with an agriculture officer.
7. Review the Agent Decision Log to inspect the processing trace.

## Project Structure

```text
SaarthiGrid_AI/
|-- app/
|   |-- app.py                  # Main Streamlit experience
|   `-- pages/
|       `-- how_it_works.py     # Architecture and methodology page
|-- src/
|   |-- agent.py                # LangGraph assembly
|   |-- nodes.py                # Six workflow nodes
|   |-- state.py                # AgentState TypedDict
|   |-- retriever.py            # CSV loading and filtering
|   |-- guardrails.py           # Input and output safety checks
|   `-- prompts.py              # LangChain prompt templates
|-- data/
|   |-- scheme_rules.csv        # 25-scheme knowledge base
|   `-- farm_profile.csv        # Five representative profiles
|-- docs/
|   |-- project_report.md       # Capstone report
|   `-- architecture.md         # Detailed technical architecture
|-- logs/
|   `-- .gitkeep                # Runtime log directory
|-- tests/
|   `-- test_cases.py           # Five pytest scenarios
|-- presentation/
|   `-- slide_content.md        # Slide narrative and speaker notes
|-- requirements.txt
|-- .env.example
|-- .gitignore
`-- README.md
```

The final MP4 and PowerPoint are distributed through the linked Drive folder to keep generated media out of Git history. The complete ZIP contains those files together with the source tree.

## Knowledge Base

Each row in `data/scheme_rules.csv` includes:

```text
scheme_id, scheme_name, launched_by, target_farmers, min_land_acres,
max_land_acres, eligible_crops, eligible_states, eligible_castes,
max_annual_income, benefit_summary, benefit_amount, documents_required,
how_to_apply, application_portal, scheme_category
```

To add or revise a scheme, update one complete row using source-backed values. Use `all` for unrestricted crops, states, or categories and `999999999` where no income ceiling applies. Run the test suite after every data revision.

## Tests

| Scenario | Profile | Expected behavior |
|---|---|---|
| HP wheat farmer | Ramesh Kumar, Mandi, 1.5 acres, SC | Valid request with multiple scheme matches |
| HP apple grower | Suresh Verma, Shimla, 3 acres | Horticulture and central scheme matches |
| Punjab rice tenant | Gurpreet Singh, Ludhiana, 0.5 acres, leased | Relevant central scheme matches |
| HP maize farmer | Birsa Munda, Kinnaur, 2 acres, ST | Crop and category-aware support matches |
| Off-topic request | Anita Devi profile with an IPL query | Guardrail blocks the request and returns no schemes |

Run the suite with:

```bash
pytest -q
```

The validated submission result is `5 passed`.

## Responsible AI

SaarthiGrid AI is a navigation assistant, not a government approval system. The retrieval layer narrows the evidence before generation, and the output validator replaces language that could imply guaranteed approval. Final eligibility may depend on official document verification, district targets, crop notifications, bank appraisal, budget availability, and current application windows.

The application does not request or store Aadhaar numbers, bank account details, certificates, or uploaded identity documents. Runtime logs record workflow metadata and scheme decisions rather than sensitive personal documents.

## Limitations

- Scheme data is curated manually and requires periodic verification.
- Application windows, subsidy rates, and annual action plans may change.
- The first release is English-first.
- District circulars and implementation quotas are not synchronized in real time.
- The system does not connect to land records, bank systems, CSC portals, or application-status APIs.
- Some schemes require facts that cannot be inferred from a short farmer profile.

## Roadmap

- Hindi, Punjabi, Marathi, and regional-language interfaces.
- Voice input and spoken responses for low-literacy users.
- WhatsApp delivery for mobile-first rural access.
- Official circular and PDF ingestion with citation-level retrieval.
- Reviewer-approved scheme synchronization.
- District dashboards for application targets and document gaps.

## Team

| Member | Role | Roll Number |
|---|---|---|
| Atharv D Khanvilkar | Team Leader | 172 |
| Dhruv Singh Gandas | Member | 226 |
| Kanish Kumar | Member | 117 |
| Modit Bagga | Member | 149 |
| Rajat Gupta | Member | 114 |

**Team:** SaarthiGrid AI  
**Project:** Farmer Subsidy and Advisory Navigation Agent  
**Track:** Agentic AI  
**Submission:** HIMSHIKHAR 2026 AAI Capstone

## License

This project is released under the MIT License.

## Acknowledgements

The team acknowledges HIMSHIKHAR 2026, IIT Mandi, Masai, the Government of India agriculture ecosystem, and the Himachal Pradesh Agriculture, Horticulture, and Animal Husbandry departments for the public scheme information used in this capstone.
