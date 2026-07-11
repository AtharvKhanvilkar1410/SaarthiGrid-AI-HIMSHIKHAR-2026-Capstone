"""Prompt templates used by SaarthiGrid AI nodes."""

from __future__ import annotations

from langchain_core.prompts import PromptTemplate


GUARDRAIL_CHECK_PROMPT = PromptTemplate(
    input_variables=["query"],
    template=(
        "Is the following query related to Indian farming, agriculture, "
        "government subsidies for farmers, or crop advisory? "
        "Answer only YES or NO.\nQuery: {query}"
    ),
)

PROFILE_PARSE_PROMPT = PromptTemplate(
    input_variables=["farmer_profile"],
    template=(
        "Convert the following farmer profile into a concise structured query for a "
        "government scheme eligibility system. Preserve factual values exactly, avoid "
        "adding assumptions, and write one sentence that includes state, district, "
        "land size, ownership, crop, caste category, annual income, and existing "
        "registrations.\n\nFarmer profile:\n{farmer_profile}"
    ),
)

ELIGIBILITY_CHECK_PROMPT = PromptTemplate(
    input_variables=["structured_query", "scheme_details"],
    template=(
        "Given this farmer profile:\n{structured_query}\n\n"
        "And this scheme:\n{scheme_details}\n\n"
        "Determine eligibility using only the stated farmer profile and scheme rules. "
        "If a required field such as age, notified crop status, bank sanction, or "
        "official verification is missing, use PARTIAL rather than making a guarantee. "
        "Return valid JSON only with double quotes and this exact shape:\n"
        "{{\n"
        '  "scheme_name": "...",\n'
        '  "verdict": "ELIGIBLE/PARTIAL/NOT_ELIGIBLE",\n'
        '  "reason": "...",\n'
        '  "confidence": "HIGH/MEDIUM/LOW"\n'
        "}}"
    ),
)

RESPONSE_GENERATION_PROMPT = PromptTemplate(
    input_variables=["name", "profile", "scheme_details", "verdict", "reason"],
    template=(
        "Generate a farmer-friendly explanation for scheme {name} for this farmer:\n"
        "{profile}\n\n"
        "Scheme details:\n{scheme_details}\n\n"
        "Eligibility verdict: {verdict}\nReason: {reason}\n\n"
        "Use simple, respectful English. Do not promise final approval; say the farmer "
        "may qualify subject to official verification where appropriate. Return valid "
        "JSON only with double quotes and this exact shape:\n"
        "{{\n"
        '  "scheme_name": "...",\n'
        '  "what_you_get": "...",\n'
        '  "eligibility_summary": "...",\n'
        '  "documents_needed": ["..."],\n'
        '  "exact_next_step": "...",\n'
        '  "portal_or_office": "..."\n'
        "}}"
    ),
)

FALLBACK_PROMPT = PromptTemplate(
    input_variables=["structured_query"],
    template=(
        "No matching scheme was found for the following farmer profile:\n"
        "{structured_query}\n\n"
        "Write a brief, farmer-friendly fallback response. Explain that the farmer "
        "should verify with the local Agriculture or Horticulture Department because "
        "district targets and annual action plans can change. Suggest improving the "
        "query by adding crop, land ownership, irrigation need, or livestock interest. "
        "Do not invent a scheme."
    ),
)
