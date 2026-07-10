"""Materials and samples extraction prompt."""

import json

from app.prompts.schemas import MATERIAL_UPDATE_JSON_SCHEMA
from app.prompts.shared_rules import (
    JSON_OUTPUT_RULES,
    SHARED_RULES,
    format_material_type_examples,
)

MATERIALS_PROMPT_TEMPLATE = """
You are the Materials and Samples module for an Enterprise Pharmaceutical CRM AI Assistant.

## Role
Extract and normalize materials shared and samples distributed during an HCP interaction.

## Extract And Normalize
- Brochures
- Leaflets
- Clinical Study
- Presentation
- Sample packs
- Sample quantities

## Normalization Examples
{material_type_examples}

## Rules
- Normalize plural and singular forms to professional CRM labels.
- Capture sample quantities when mentioned.
- Return empty arrays when no materials or samples were mentioned.
- Never invent materials or sample inventory.

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
    """Build the materials and samples prompt."""
    return MATERIALS_PROMPT_TEMPLATE.format(
        material_type_examples=format_material_type_examples(),
        conversation_history=conversation_history,
        current_interaction=current_interaction,
        user_instruction=user_instruction,
        json_schema=json.dumps(MATERIAL_UPDATE_JSON_SCHEMA, ensure_ascii=True, indent=2),
        shared_rules=SHARED_RULES,
        json_output_rules=JSON_OUTPUT_RULES,
    )
