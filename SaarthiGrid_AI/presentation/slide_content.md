# SaarthiGrid AI Presentation Content

## Slide 1: Title

**SaarthiGrid AI**  
Farmer Subsidy and Advisory Navigation Agent  
Agentic AI Capstone | Team SaarthiGrid AI

**Speaker Notes:**  
Good morning. We are presenting SaarthiGrid AI, a farmer subsidy and advisory navigation agent designed as an Agentic AI capstone. The project helps farmers understand which government schemes may fit their farm profile, what documents they need, and where to apply. Our focus is not just building a chatbot, but building an auditable AI workflow for responsible public-service navigation.

## Slide 2: The Problem

- India has millions of small and marginal agricultural households; NSS 77th round data reported 89.4% of agricultural households owning less than two hectares.
- Farmers face fragmented scheme information across central portals, state departments, banks, CSCs, and district offices.
- NABARD/PIB rural financial inclusion reporting shows rural income and savings are improving, but formal access still depends on correct records and process navigation.
- Pain points: language, paperwork, eligibility complexity, seasonal deadlines, and low trust in informal advice.

**Speaker Notes:**  
The problem is not that India lacks farmer schemes. The problem is that farmers often cannot map their own situation to the correct scheme. A farmer may know about PM-KISAN but not about insurance, irrigation, equipment, horticulture, or state-specific support. Small landholders are especially affected because they have limited time, limited paperwork support, and high risk if they miss an application window.

## Slide 3: Our Solution

- One-line pitch: SaarthiGrid AI turns a farmer profile into clear, scheme-specific eligibility guidance.
- Key features:
  - Central and Himachal Pradesh scheme database.
  - LangGraph agent pipeline.
  - Deterministic rule filtering.
  - LLM-based explanation with offline fallback.
  - Guardrails against off-topic queries and false guarantees.
  - Streamlit UI with decision log.
- Helps farmers, extension workers, student researchers, and rural service operators.

**Speaker Notes:**  
SaarthiGrid AI asks for practical details: state, district, crop, land size, ownership, caste category, income, and registrations. It then checks a structured scheme rule base and generates a simple answer: which schemes may fit, why, documents needed, and the exact next step. We designed it to support human decision-making, not replace official approval by departments or banks.

## Slide 4: System Architecture

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
 [CSV Scheme Matcher] <---- scheme_rules.csv
        |
        v
 [Eligibility Checker]
        |
        v
 [Response Generator]
        |
        v
 [Logger Node] ----> logs/agent_log.json
```

- UI layer: Streamlit.
- Orchestration layer: LangGraph.
- Knowledge layer: CSV scheme rules.
- Reasoning layer: LLM or deterministic fallback.
- Audit layer: decision logs.

**Speaker Notes:**  
This architecture is intentionally explicit. Each node has one responsibility, and each state transition is visible in the log. The guardrail node protects scope, the parser validates profile data, the matcher retrieves schemes, the eligibility checker reasons about partial conditions, and the generator explains next steps. The logger creates traceability, which is essential for responsible AI in government-facing use cases.

## Slide 5: AI Innovation

- Why LangGraph, not a simple chatbot:
  - State is inspectable.
  - Routing is explicit.
  - Each node can be tested independently.
  - Guardrail failures stop early.
- RAG in simple terms:
  - Retrieve verified scheme rows.
  - Reason only over matched evidence.
  - Generate farmer-friendly guidance.
- Responsible AI:
  - No approval guarantees.
  - Blocked off-domain topics.
  - Output hedging validator.

**Speaker Notes:**  
A simple chatbot can sound helpful while hiding how it reached an answer. LangGraph gives us a controlled workflow, more like a decision pipeline. Our RAG approach does not ask the model to memorize schemes. Instead, it retrieves verified scheme data first and asks the model to explain it. If an API key is unavailable, the system still runs with deterministic fallback logic.

## Slide 6: Data and Knowledge Base

- 25 schemes in `scheme_rules.csv`.
- 15 central schemes:
  PM-KISAN, PMFBY, PM-KMY, KCC, Soil Health Card, PMKSY, eNAM, AIF, PKVY, MIDH, RKVY, NLM, NFSM/NFSNM, NMSA, SMAM.
- 10 Himachal Pradesh schemes:
  natural farming, fencing, horticulture, beekeeping, polyhouse, irrigation, SC/ST equipment, seed subsidy, goat rearing, mushroom cultivation.
- Fields include state, crop, caste, land, income, documents, benefit, portal, and category.
- Sources include official central and HP department portals.

**Speaker Notes:**  
The knowledge base is the heart of the project. We did not use dummy schemes. Each row represents a real scheme and includes the columns needed for eligibility filtering and farmer guidance. The database is deliberately stored as CSV so reviewers can inspect it, update it, and test it. This is more maintainable than burying scheme facts inside prompts or model memory.

## Slide 7: Live Demo Screenshots

[Insert Streamlit screenshot here]

Annotations:
- Sidebar: farmer profile form.
- Main result area: matched schemes and verdicts.
- Expander: benefits, documents, next step, portal.
- Bottom expander: agent decision log.

**Speaker Notes:**  
In the live demo, we enter a farmer profile such as Ramesh Kumar from Mandi with 1.5 acres of wheat and SC category. The agent checks central and Himachal Pradesh schemes, then shows green eligible and yellow partial recommendations. The key demo point is the decision log: we can show exactly how the query moved through guardrail, parsing, matching, eligibility checking, response generation, and logging.

## Slide 8: Test Results

| Test Farmer | Profile | Expected Result | Observed Behavior |
|---|---|---|---|
| Ramesh Kumar | HP, wheat, SC, 1.5 acres | At least 2 schemes | Multiple central and HP matches |
| Suresh Verma | HP, apple, General, 3 acres | At least 2 schemes | Horticulture, insurance, irrigation matches |
| Gurpreet Singh | Punjab, rice, OBC, leased | At least 2 schemes | Central schemes and partial credit/insurance |
| Birsa Munda | HP, maize, ST, 2 acres | At least 2 schemes | NFSM, seed, equipment, irrigation matches |
| Anita Devi | Off-topic IPL query | Blocked | Guardrail returns redirect and no schemes |

- Guardrail test result: off-topic query blocked.
- Accuracy assessment: deterministic filters match encoded rules; partial verdicts protect uncertain cases.

**Speaker Notes:**  
Our tests validate both positive and negative behavior. Four valid farming profiles must pass guardrails and produce at least two scheme matches. The fifth test uses a real farmer profile but asks an off-topic IPL query, which must be blocked. This matters because public-service AI should be useful, but also disciplined about scope and careful about overclaiming eligibility.

## Slide 9: Limitations and Responsible Use

- The system does not approve applications.
- It does not replace agriculture officers, banks, CSCs, or official portals.
- It does not verify land records, Aadhaar, caste certificates, or bank sanction.
- Data freshness depends on updating `scheme_rules.csv`.
- English-only interface is a current accessibility limitation.
- The agent says "may qualify" because final approval depends on official verification.

**Speaker Notes:**  
Responsible use is central to this project. SaarthiGrid AI is a navigation assistant, not an authority. It can reduce confusion, but it cannot certify a farmer's application. Many schemes depend on district targets, current budget, notified crops, and documents. That is why our responses are careful and why the architecture logs the reasoning instead of presenting the answer as a black box.

## Slide 10: Future Scope and Conclusion

- Future improvements:
  - Hindi, Punjabi, and regional language support.
  - Real-time official scheme database sync.
  - WhatsApp and mobile integration.
  - Voice input and assisted form filling.
  - District officer dashboard.
- Impact potential:
  - Faster scheme discovery.
  - Better document readiness.
  - Stronger trust through transparency.

Thank you. Q&A.

**Speaker Notes:**  
The next step is to move from a strong capstone prototype to a field-ready assistant. That means regional languages, voice input, WhatsApp delivery, and a live scheme update workflow. We also see value for extension workers who advise many farmers. SaarthiGrid AI shows how agentic AI can responsibly support farmers by making public schemes easier to understand and act on.
