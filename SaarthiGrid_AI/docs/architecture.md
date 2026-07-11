# SaarthiGrid AI Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Streamlit UI                            │
│  Sidebar farm profile form | Query box | Result cards | Logs    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ AgentState
                                v
┌─────────────────────────────────────────────────────────────────┐
│                         LangGraph                               │
│                                                                 │
│  guardrail_node                                                  │
│      ├── invalid query ───────────────► END                     │
│      └── valid query                                            │
│              v                                                  │
│  profile_parser_node                                            │
│              v                                                  │
│  scheme_matcher_node ───────────────► data/scheme_rules.csv     │
│              v                                                  │
│  eligibility_checker_node ─────────► OpenAI LLM or fallback     │
│              v                                                  │
│  response_generator_node ──────────► output guardrails          │
│              v                                                  │
│  logger_node ──────────────────────► logs/agent_log.json        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. The farmer enters name, state, district, land size, ownership, crop, caste, income, registrations, and an optional query in Streamlit.
2. The UI builds an `AgentState` object containing the farmer profile, raw query, empty result lists, and empty log list.
3. `guardrail_node` checks blocked terms and verifies that the query is related to Indian farming, government farmer schemes, or crop advisory.
4. If the query is blocked, LangGraph routes directly to `END`. The state includes a polite redirect message and no matched schemes.
5. `profile_parser_node` validates required profile fields and creates a structured profile sentence.
6. `scheme_matcher_node` loads `scheme_rules.csv` with pandas and filters by state, land range, crop, caste category, and income.
7. `eligibility_checker_node` asks the LLM to classify matched schemes. If no LLM is configured, deterministic fallback logic creates conservative verdicts.
8. `response_generator_node` creates structured response cards for `ELIGIBLE` and `PARTIAL` schemes. Output validation hedges risky claims.
9. `logger_node` appends a complete run record to `logs/agent_log.json`.
10. The UI renders result expanders, document lists, next steps, official portal links, and the agent decision log.

## LangGraph State Transitions

```
START
  |
  v
guardrail_node
  |-- is_valid_query == False --> END
  |
  v
profile_parser_node
  |
  v
scheme_matcher_node
  |
  v
eligibility_checker_node
  |
  v
response_generator_node
  |
  v
logger_node
  |
  v
END
```

The shared state is a `TypedDict` with these fields:

```
farmer_profile: dict
raw_query: str
is_valid_query: bool
guardrail_message: str
structured_query: str
matched_schemes: list[dict]
eligibility_results: list[dict]
final_response: str
agent_log: list[dict]
error: str
```

## Guardrail Decision Tree

```
                    ┌───────────────────┐
                    │ Receive raw query │
                    └─────────┬─────────┘
                              v
                    ┌───────────────────┐
                    │ Empty query?      │
                    └──────┬────────────┘
                           │ yes
                           v
                    Treat as valid profile-led search
                           │
                           v
┌─────────────────┐   no   ┌──────────────────────────────────┐
│ Blocklist term? │◄───────┤ cricket, IPL, politics, stocks... │
└──────┬──────────┘        └──────────────────────────────────┘
       │ yes
       v
Return farming redirect and END
       │ no
       v
┌───────────────────────────────┐
│ LLM or heuristic domain check │
└──────────────┬────────────────┘
               │ NO
               v
Return farming redirect and END
               │ YES
               v
Continue to profile parser
```

## RAG Pipeline

SaarthiGrid uses structured RAG rather than vector-only retrieval. The retrieval source is a curated CSV rule base.

```
                 ┌────────────────────────────┐
                 │ data/scheme_rules.csv      │
                 │ 25 verified scheme records │
                 └──────────────┬─────────────┘
                                │ pandas load
                                v
┌──────────────────┐    deterministic filters    ┌───────────────────┐
│ Farmer profile   │ ───────────────────────────► │ Matched schemes   │
│ state, crop,     │                              │ exact rule subset │
│ land, caste,     │                              └─────────┬─────────┘
│ income           │                                        │
└──────────────────┘                                        v
                                                  ┌───────────────────┐
                                                  │ Eligibility LLM   │
                                                  │ or fallback       │
                                                  └─────────┬─────────┘
                                                            v
                                                  ┌───────────────────┐
                                                  │ Grounded answer   │
                                                  │ + next steps      │
                                                  └───────────────────┘
```

Why this form of RAG:

- Scheme rules are structured, so exact filters are safer than semantic similarity for eligibility.
- CSV records are easy to audit, update, and test.
- LLM calls operate after retrieval, reducing hallucination risk.
- Response cards cite documents and portals already stored in the retrieved row.

## Component Dependency Map

```
app/app.py
  └── src.agent.app_graph
        ├── src.state.AgentState
        └── src.nodes
              ├── src.guardrails
              │     └── src.prompts.GUARDRAIL_CHECK_PROMPT
              ├── src.prompts
              ├── src.retriever
              │     └── pandas
              ├── langchain_openai.ChatOpenAI
              └── logs/agent_log.json

tests/test_cases.py
  └── src.agent.app_graph
        └── deterministic fallback when OPENAI_API_KEY is unset
```

## Error Handling

- Missing profile fields set `error` and create a clear final response.
- Missing or malformed CSV data is caught in `scheme_matcher_node`.
- LLM invocation failures fall back to deterministic reasoning.
- Invalid JSON from the LLM is ignored and replaced with local structured output.
- Streamlit catches graph-level exceptions and displays a user-facing error.

## Security and Privacy Notes

The demo does not collect Aadhaar numbers, bank account numbers, or uploaded documents. It records only profile summaries and scheme decisions in local logs. For deployment, logs should be stored with access controls, personally identifying fields should be minimized or hashed, and retention should be limited by policy.
