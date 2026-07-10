"""HCP search prompt for structured search query generation."""

import json

from app.prompts.schemas import HCP_SEARCH_JSON_SCHEMA
from app.prompts.shared_rules import JSON_OUTPUT_RULES, SEARCH_RULES, SHARED_RULES

SEARCH_HCP_PROMPT_TEMPLATE = """
You are the HCP Search module for an Enterprise Pharmaceutical CRM AI Assistant.

## Role
Generate search-friendly structured queries from the user's natural language request.

## Understand And Structure
- Doctor name, including partial names
- Hospital or institution
- City
- State
- Specialization
- Typographical mistakes and alternate spellings

## Rules
- Never fabricate HCP records.
- Preserve multiple plausible search terms when the user is uncertain.
- Return null for filters that were not mentioned.

## Conversation History
{conversation_history}

## Current HCP Context
{current_hcp}

## User Query
{user_query}

## Output Contract
Return STRICT JSON only.
Use this JSON schema:
{json_schema}

{shared_rules}

{search_rules}

{json_output_rules}
""".strip()


def build(
    *,
    conversation_history: str,
    current_hcp: str,
    user_query: str,
) -> str:
    """Build the HCP search prompt."""
    return SEARCH_HCP_PROMPT_TEMPLATE.format(
        conversation_history=conversation_history,
        current_hcp=current_hcp,
        user_query=user_query,
        json_schema=json.dumps(HCP_SEARCH_JSON_SCHEMA, ensure_ascii=True, indent=2),
        shared_rules=SHARED_RULES,
        search_rules=SEARCH_RULES,
        json_output_rules=JSON_OUTPUT_RULES,
    )
