# SaarthiGrid AI Project Report

## 1. Executive Summary

SaarthiGrid AI is a farmer subsidy and advisory navigation agent built as an Agentic AI capstone. The system helps Indian farmers discover central and Himachal Pradesh government schemes by converting a farm profile into a structured eligibility query, retrieving matching schemes from a curated rule base, checking eligibility, and generating farmer-friendly next steps. The first release focuses on 25 real schemes, including PM-KISAN, PMFBY, KCC, Soil Health Card, Agriculture Infrastructure Fund, and 10 Himachal Pradesh state-level agriculture, horticulture, irrigation, livestock, and mechanization schemes. The core users are small and marginal farmers, extension workers, rural entrepreneurs, and student teams demonstrating responsible AI for public-service navigation. The project matters because subsidy access is often constrained not by the absence of policy, but by fragmented information, paperwork ambiguity, district-specific implementation windows, and low confidence about where to apply.

## 2. Problem Statement

India has one of the largest public agriculture support ecosystems in the world, yet the practical journey from "a scheme exists" to "this farmer can apply correctly" remains difficult. Farmers must interpret central guidelines, state annual action plans, district targets, banking rules, caste-specific provisions, land records, crop notifications, and department portals. For a small farmer, this information is scattered across ministry pages, district offices, bank branches, Common Service Centres, and informal advice networks.

The scale is substantial. The Government of India has reported, using the NSS 77th round Situation Assessment Survey, that 89.4% of agricultural households own less than two hectares of land, making the typical farmer small or marginal rather than a large commercial operator. NABARD's rural financial inclusion reporting, summarized by PIB for NAFIS 2021-22, also shows that rural household incomes and savings are changing, but formal financial inclusion still requires careful last-mile navigation. Kisan Credit Card access, crop insurance enrollment, direct benefit transfers, and infrastructure loans all depend on correct records, documentation, and timing.

Existing solutions fall short because they are usually either static lists of schemes or broad chatbots without auditable reasoning. Static portals provide official information but do not personalize it. Generic chatbots may sound fluent but can hallucinate eligibility or overpromise approval. SaarthiGrid AI addresses this gap by combining deterministic retrieval from a structured rule base with guarded LLM explanations.

## 3. Solution Architecture

SaarthiGrid AI uses a LangGraph state machine rather than a single chatbot call. The decision pipeline is explicit: guardrail, profile parser, scheme matcher, eligibility checker, response generator, and logger. Each node updates a shared `AgentState`, allowing reviewers to inspect the inputs, filters, verdicts, final answer, and audit trail.

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
 [Eligibility Checker] <---- LLM or deterministic fallback
        |
        v
 [Response Generator] <---- output guardrails
        |
        v
 [Logger Node] ----> logs/agent_log.json
```

The project uses retrieval-augmented generation instead of fine-tuning. Fine-tuning would teach a model patterns of scheme language but would not guarantee data freshness, traceability, or exact rule adherence. Government schemes change through annual action plans, state circulars, and budget allocations. A CSV knowledge base can be updated, reviewed, versioned, and tested without retraining a model. The LLM is therefore used for interpretation and explanation, while eligibility filtering begins with deterministic rules.

The guardrail node protects scope. It blocks queries about cricket, films, stock markets, politics, elections, and other off-domain topics, then uses an LLM or local heuristic to confirm that the query belongs to farming, subsidies, or crop advisory. The profile parser validates required fields and produces a concise structured profile sentence. The scheme matcher applies hard filters: state, land range, crop, caste, and income. The eligibility checker adds nuance for partial cases such as crop insurance notification, pension age, bank sanction, and project verification. The response generator turns these results into farmer-readable cards with documents and next steps, using hedged language such as "may qualify" rather than "will receive." The logger preserves an auditable run record.

## 4. Implementation Details

The technical stack is intentionally lightweight and inspectable. Python provides the core runtime. Pandas loads and filters `scheme_rules.csv`. LangGraph manages the node pipeline. LangChain prompt templates keep prompts centralized and testable. `langchain-openai` is used when an OpenAI API key is configured, while deterministic fallback logic keeps tests and classroom demonstrations runnable without network calls. Streamlit provides a usable front end with a sidebar farmer profile form, result expanders, portal buttons, verdict colors, and a decision log.

The data collection approach prioritizes real official scheme facts over synthetic content. The central scheme entries were structured from official pages and guidelines such as PM-KISAN, PMFBY, PM-KMY, Soil Health Card, PMKSY, eNAM, AIF, PKVY, MIDH, NFSM/NFSNM, NMSA, SMAM, and NLM. The Himachal Pradesh entries were mapped from HP Agriculture, HP Horticulture/eUdyan, and HP Animal Husbandry portals. Each scheme row includes rule fields needed for matching plus benefit summary, application route, documents, portal, and category.

Key tradeoffs were made. First, the CSV uses simplified eligibility filters because real scheme approval may depend on age, notified village/crop, annual district target, bank appraisal, or departmental inspection. Instead of pretending these are known, the system returns `PARTIAL` when verification is required. Second, the project avoids a vector database in the first release because the current knowledge base is structured and small; deterministic filtering is more explainable than embedding similarity for exact eligibility. Third, the system stores run logs locally for transparency but avoids storing sensitive documents, bank numbers, or Aadhaar numbers.

The implementation also separates "matching" from "recommendation." A scheme can pass the hard filters and still receive a partial verdict because the farmer must satisfy a secondary process outside the profile, such as PMFBY crop notification, AIF bank appraisal, or HP department site inspection. This separation is important for public-sector AI because it prevents the model from collapsing uncertainty into a false yes/no answer. The same design supports future expansion: new schemes can be added by extending the CSV, while richer document retrieval can later be added without changing the UI contract.

## 5. Results and Evaluation

The test suite covers five farmer profiles. Ramesh Kumar, an SC wheat farmer in Mandi with 1.5 acres, matches central income, insurance, soil, irrigation, food security, mechanization, HP natural farming, HP crop protection, HP irrigation, HP seed subsidy, and HP SC/ST equipment support. Suresh Verma, an apple grower in Shimla, matches horticulture, beekeeping, crop insurance, natural farming, crop protection, and irrigation pathways. Gurpreet Singh, a leased rice farmer in Punjab, still receives crop insurance, KCC, soil, eNAM, NFSM, PMKSY, NMSA, and other central options, while landholding-only schemes are treated carefully. Birsa Munda, an ST maize farmer in Kinnaur, receives strong matches for NFSM, HP seed subsidy, HP equipment subsidy, and irrigation. Anita Devi's profile is used in an off-topic guardrail test by asking about IPL; the agent blocks the query and returns no schemes.

The scheme matcher is accurate for the encoded rule fields because it uses deterministic comparisons. The eligibility layer is deliberately conservative where rules need verification. Guardrails are effective against explicit blocked topics and against non-agricultural queries through LLM or heuristic classification.

Evaluation is not presented as official legal eligibility. Instead, it checks whether the system behaves correctly for its stated role: narrowing a farmer's search space, flagging likely and partial matches, preserving a decision trail, and refusing off-domain requests. The decision log is especially useful for review because it records matched scheme counts and the names of retrieved schemes. This makes errors easier to diagnose than in a one-shot chatbot response.

## 6. Responsible AI and Limitations

The main hallucination risk is an LLM inventing eligibility or implying guaranteed approval. SaarthiGrid mitigates this by grounding retrieval in a CSV rule base, logging every step, and running output validation that removes phrases such as "you will receive" or "guaranteed." The agent says "may qualify" because government approval depends on official verification, budget availability, crop notification, land records, bank appraisal, and district targets.

The data freshness limitation is real. Scheme portals and annual action plans can change, especially subsidy percentages and application windows. The first release is English-only, which limits accessibility for many farmers who would prefer Hindi, Punjabi, Marathi, or local dialects. It also does not yet integrate live land-record, bank, or department APIs.

## 7. Future Improvements

Future versions should add Hindi and Punjabi interfaces, voice input for low-literacy users, and WhatsApp delivery for mobile-first access. The scheme database should sync with official portals and state circulars through a controlled review workflow. A district officer mode could show pending applications, document gaps, and local targets. The RAG layer can later include official PDFs and circulars with citations once document ingestion is added.

## 8. Conclusion

SaarthiGrid AI demonstrates how agentic AI can support public-service navigation without replacing official approval systems. Its value lies in narrowing the gap between a farmer's profile and the schemes that may fit that profile. By combining structured data, deterministic filtering, conservative LLM reasoning, guardrails, and transparent logs, the project offers a production-quality foundation for responsible agricultural advisory tooling.

## Sources Used

- PM-KISAN official portal: https://pmkisan.gov.in/
- PMFBY official portal and feature document: https://pmfby.gov.in/
- PM-KMY PIB release: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2053142
- Agriculture Infrastructure Fund portal: https://agriinfra.dac.gov.in/
- NFSM/NFSNM portal: https://www.nfsm.gov.in/
- NMSA portal: https://nmsa.dac.gov.in/
- HP Agriculture schemes: https://agriculture.hp.gov.in/en/our-scheme/
- HP Horticulture/eUdyan services: https://eudyan.hp.gov.in/Department/Portal/CitizenServices.aspx
- HP Animal Husbandry DBT: https://hpahdbt.hp.gov.in/
- PIB on small and marginal agricultural households: https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1910357
- PIB on NABARD NAFIS 2021-22: https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=153270&lang=1
