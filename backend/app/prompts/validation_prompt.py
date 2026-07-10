"""Validation prompt for structured CRM outputs."""

import json
from typing import Any

from app.prompts.schemas import VALIDATION_RESULT_JSON_SCHEMA
from app.prompts.shared_rules import JSON_OUTPUT_RULES, SHARED_RULES, format_sentiment_options

VALIDATION_PROMPT_TEMPLATE = """
You are the Validation module for an Enterprise Pharmaceutical CRM AI Assistant.

## Role
Validate tool outputs, structured payloads, and CRM business constraints.

## Validate
- Missing required fields
- Incorrect dates
- Malformed JSON structures
- Unknown or unsupported values
- Sentiment normalization
- Interaction type normalization

## Allowed Sentiment Values
{sentiment_options}

## Selected Tool
{selected_tool}

## Tool Result
{tool_result}

## Current Interaction Draft
{interaction_draft}

## Prior Validation Errors
{prior_errors}

## Output Contract
Return STRICT JSON only.
Use this JSON schema:
{json_schema}

If invalid, provide precise suggestions for correction.

{shared_rules}

{json_output_rules}
""".strip()


def build(
    *,
    selected_tool: str,
    tool_result: str | dict[str, Any],
    interaction_draft: str | dict[str, Any],
    prior_errors: str | list[str],
) -> str:
    """Build the validation prompt."""
    tool_payload = (
        tool_result if isinstance(tool_result, str) else json.dumps(tool_result, ensure_ascii=True)
    )
    draft_payload = (
        interaction_draft
        if isinstance(interaction_draft, str)
        else json.dumps(interaction_draft, ensure_ascii=True)
    )
    errors_payload = (
        prior_errors if isinstance(prior_errors, str) else json.dumps(prior_errors, ensure_ascii=True)
    )

    return VALIDATION_PROMPT_TEMPLATE.format(
        sentiment_options=format_sentiment_options(),
        selected_tool=selected_tool,
        tool_result=tool_payload,
        interaction_draft=draft_payload,
        prior_errors=errors_payload,
        json_schema=json.dumps(VALIDATION_RESULT_JSON_SCHEMA, ensure_ascii=True, indent=2),
        shared_rules=SHARED_RULES,
        json_output_rules=JSON_OUTPUT_RULES,
    )
