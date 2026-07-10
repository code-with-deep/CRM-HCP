"""Edit interaction prompt for surgical CRM draft updates."""

import json
from typing import Any

from app.prompts.schemas import EDIT_INTERACTION_JSON_SCHEMA
from app.prompts.shared_rules import EDIT_RULES, JSON_OUTPUT_RULES, SHARED_RULES, format_sentiment_options

EDIT_INTERACTION_PROMPT_TEMPLATE = """
You are the Edit Interaction module for an Enterprise Pharmaceutical CRM AI Assistant.

## Role
Modify ONLY the interaction fields explicitly requested by the user.

## Inputs
Current interaction:
{current_interaction}

Conversation history:
{conversation_history}

User instruction:
{user_instruction}

## Rules
- Keep all unchanged fields exactly as they appear in the current interaction.
- Return the COMPLETE updated interaction JSON, not a partial patch.
- Normalize sentiment to one of: {sentiment_options}
- Return null for fields that should remain unset unless the user changed them.

## Output Contract
Return STRICT JSON only.
Use this JSON schema:
{json_schema}

{shared_rules}

{edit_rules}

{json_output_rules}
""".strip()


def build(
    *,
    current_interaction: str | dict[str, Any],
    conversation_history: str | list[dict[str, Any]],
    user_instruction: str,
) -> str:
    """Build the edit interaction prompt."""
    interaction_payload = (
        current_interaction
        if isinstance(current_interaction, str)
        else json.dumps(current_interaction, ensure_ascii=True)
    )
    history_payload = (
        conversation_history
        if isinstance(conversation_history, str)
        else json.dumps(conversation_history, ensure_ascii=True)
    )

    return EDIT_INTERACTION_PROMPT_TEMPLATE.format(
        current_interaction=interaction_payload,
        conversation_history=history_payload,
        user_instruction=user_instruction,
        sentiment_options=format_sentiment_options(),
        json_schema=json.dumps(EDIT_INTERACTION_JSON_SCHEMA, ensure_ascii=True, indent=2),
        shared_rules=SHARED_RULES,
        edit_rules=EDIT_RULES,
        json_output_rules=JSON_OUTPUT_RULES,
    )
