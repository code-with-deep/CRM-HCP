"""Follow-up and outcome extraction prompt."""

import json

from app.prompts.schemas import FOLLOW_UP_UPDATE_JSON_SCHEMA
from app.prompts.shared_rules import JSON_OUTPUT_RULES, SHARED_RULES

FOLLOWUP_PROMPT_TEMPLATE = """
You are the Follow-up and Outcome module for an Enterprise Pharmaceutical CRM AI Assistant.

## Role
Extract outcomes, next actions, reminders, and follow-up dates from the user's message.

## Extract
- Outcome
- Next action
- Reminder
- Follow-up date
- Suggested follow-up summary

## Rules
- Use ISO date format YYYY-MM-DD for follow_up_date when present.
- Return null for missing values.
- Preserve existing outcomes or follow-up text unless the user explicitly changes them.
- Generate a professional suggested_follow_up_summary when enough context exists.

## Conversation History
{conversation_history}

## Current Interaction Draft
{current_interaction}

## User Instruction
{user_instruction}

## Output Contract
Return STRICT JSON only.
Use this JSON schema:
{json_schema}

{shared_rules}

{json_output_rules}
""".strip()


def build(
    *,
    conversation_history: str,
    current_interaction: str,
    user_instruction: str,
) -> str:
    """Build the follow-up extraction prompt."""
    return FOLLOWUP_PROMPT_TEMPLATE.format(
        conversation_history=conversation_history,
        current_interaction=current_interaction,
        user_instruction=user_instruction,
        json_schema=json.dumps(FOLLOW_UP_UPDATE_JSON_SCHEMA, ensure_ascii=True, indent=2),
        shared_rules=SHARED_RULES,
        json_output_rules=JSON_OUTPUT_RULES,
    )
