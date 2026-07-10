"""Reusable prompt rules shared across Healthcare CRM AI prompts."""

from enum import Enum


class SentimentValue(str, Enum):
    """Normalized sentiment values for interaction logging."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


SENTIMENT_VALUES: tuple[str, ...] = (
    SentimentValue.POSITIVE.value,
    SentimentValue.NEUTRAL.value,
    SentimentValue.NEGATIVE.value,
)

INTERACTION_TYPE_EXAMPLES: tuple[str, ...] = (
    "Face to Face",
    "Call",
    "Virtual Meeting",
    "Conference",
    "Meeting",
)

MATERIAL_TYPE_EXAMPLES: tuple[str, ...] = (
    "Brochure",
    "Clinical Study",
    "Product Leaflet",
    "Presentation",
)

SHARED_RULES = """
## Shared CRM AI Rules

1. Never hallucinate medical, clinical, or HCP information.
2. Never invent HCP identities, hospitals, products, or interaction details that are not present in the user message.
3. DO extract HCP names, dates (including "today"), topics, products, materials, and samples that ARE clearly present.
4. Never overwrite unchanged fields during edits.
5. Only update values explicitly requested by the user or clearly inferred from the latest message.
6. If data is missing or uncertain, return null instead of inventing information.
7. Prefer ISO-8601 date format (YYYY-MM-DD) and 24-hour or clearly labeled local time strings.
8. Normalize product names to canonical capitalization when confidently known.
9. Normalize sentiment to exactly one of: positive, neutral, negative.
10. Normalize interaction types to professional CRM labels such as Face to Face, Call, Virtual Meeting, Meeting, or Conference.
11. Always return valid JSON when structured output is requested.
12. Do not generate prose when a prompt requests strict JSON only.
13. Preserve existing interaction draft context only for edit/update tools — never when logging a new interaction.
14. When logging a new interaction, extract only from the latest user message and ignore stale draft values.
15. Use professional pharmaceutical and healthcare CRM terminology.
16. Treat all outputs as enterprise audit-relevant records.
17. Prefer completing a CRM action with partial data over asking unnecessary clarifying questions.
""".strip()

JSON_OUTPUT_RULES = """
## JSON Output Rules

- Return only valid JSON matching the requested schema.
- Use null for unknown or missing fields.
- Use arrays for list fields even when empty.
- Do not include markdown fences unless explicitly requested.
- Do not include explanatory prose outside the JSON payload.
""".strip()

EDIT_RULES = """
## Edit Rules

- Modify ONLY the fields the user explicitly asked to change.
- Keep all other interaction fields exactly as provided in the current interaction draft.
- Return the complete updated interaction object, not a partial patch, when requested.
- If the user corrects a prior value, replace only that corrected field.
""".strip()

SEARCH_RULES = """
## Search Rules

- Generate search-friendly structured queries from natural language.
- Support partial doctor names, hospital names, cities, states, and specializations.
- Tolerate typographical mistakes by preserving multiple plausible search terms.
- Never fabricate HCP records; only structure what the user is looking for.
""".strip()


def format_sentiment_options() -> str:
    """Return comma-separated sentiment options for prompt injection."""
    return ", ".join(SENTIMENT_VALUES)


def format_interaction_type_examples() -> str:
    """Return interaction type examples for prompt injection."""
    return ", ".join(INTERACTION_TYPE_EXAMPLES)


def format_material_type_examples() -> str:
    """Return material type examples for prompt injection."""
    return ", ".join(MATERIAL_TYPE_EXAMPLES)
