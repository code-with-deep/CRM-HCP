"""JSON schema definitions for prompt-driven structured outputs."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.prompts.shared_rules import SENTIMENT_VALUES


class InteractionSchema(BaseModel):
    """Canonical structured interaction payload for CRM logging."""

    model_config = ConfigDict(extra="forbid")

    hcp_name: str | None = Field(default=None, description="Healthcare professional name.")
    interaction_type: str | None = Field(default=None, description="Interaction channel or meeting type.")
    interaction_date: str | None = Field(default=None, description="ISO date in YYYY-MM-DD format.")
    interaction_time: str | None = Field(default=None, description="Interaction time string.")
    attendees: list[str] = Field(default_factory=list, description="Attendee names.")
    products: list[str] = Field(default_factory=list, description="Products discussed.")
    topics_discussed: list[str] = Field(default_factory=list, description="Discussion topics.")
    materials_shared: list[str] = Field(default_factory=list, description="Materials shared with the HCP.")
    samples_distributed: list[str] = Field(default_factory=list, description="Samples distributed.")
    sentiment: str | None = Field(
        default=None,
        description=f"Observed sentiment: one of {', '.join(SENTIMENT_VALUES)}.",
    )
    outcomes: str | None = Field(default=None, description="Key outcomes or agreements.")
    follow_up_actions: str | None = Field(default=None, description="Follow-up actions or reminders.")
    additional_notes: str | None = Field(default=None, description="Additional notes.")
    professional_summary: str | None = Field(
        default=None,
        description="Professional CRM summary of the interaction.",
    )


class LogInteractionOutput(InteractionSchema):
    """Structured output for log interaction extraction."""

    fields_populated: list[str] = Field(
        default_factory=list,
        description="Interaction fields populated from the user message.",
    )


class EditInteractionRequest(BaseModel):
    """Structured edit request context for interaction updates."""

    model_config = ConfigDict(extra="forbid")

    user_instruction: str = Field(description="Latest user instruction for the edit.")
    current_interaction: InteractionSchema = Field(
        description="Current interaction draft that must be preserved except for requested edits.",
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Recent conversation history for edit context.",
    )


class EditInteractionOutput(InteractionSchema):
    """Complete updated interaction after a surgical edit."""

    fields_updated: list[str] = Field(
        default_factory=list,
        description="Fields modified during this edit operation.",
    )


class HcpSearchRequest(BaseModel):
    """Structured HCP search query."""

    model_config = ConfigDict(extra="forbid")

    query_text: str | None = Field(default=None, description="Free-text search query.")
    doctor_name: str | None = Field(default=None, description="Doctor or HCP name, including partial names.")
    hospital: str | None = Field(default=None, description="Hospital or institution.")
    city: str | None = Field(default=None, description="City filter.")
    state: str | None = Field(default=None, description="State or region filter.")
    specialization: str | None = Field(default=None, description="Medical specialization.")
    alternate_spellings: list[str] = Field(
        default_factory=list,
        description="Alternate spellings or typo-tolerant variants.",
    )


class HcpSearchOutput(BaseModel):
    """Structured output for HCP search prompt reasoning."""

    model_config = ConfigDict(extra="forbid")

    search_request: HcpSearchRequest
    search_reasoning: str = Field(description="Why these search parameters were selected.")


class MaterialUpdateSchema(BaseModel):
    """Structured materials and samples update payload."""

    model_config = ConfigDict(extra="forbid")

    materials_shared: list[str] = Field(
        default_factory=list,
        description="Normalized materials such as brochures, leaflets, clinical studies, presentations.",
    )
    samples_distributed: list[str] = Field(
        default_factory=list,
        description="Normalized sample names or sample packs distributed.",
    )
    sample_quantities: dict[str, int] = Field(
        default_factory=dict,
        description="Sample name to quantity distributed mapping.",
    )
    notes: str | None = Field(default=None, description="Optional notes about materials or samples.")


class FollowUpUpdateSchema(BaseModel):
    """Structured follow-up and outcome update payload."""

    model_config = ConfigDict(extra="forbid")

    outcomes: str | None = Field(default=None, description="Key outcomes or agreements.")
    follow_up_actions: str | None = Field(default=None, description="Next actions or reminders.")
    follow_up_date: str | None = Field(default=None, description="ISO follow-up date if mentioned.")
    reminder: str | None = Field(default=None, description="Reminder text for the representative.")
    suggested_follow_up_summary: str | None = Field(
        default=None,
        description="Suggested professional follow-up summary.",
    )


class PromptValidationResult(BaseModel):
    """Structured validation result for prompt-layer validation."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    normalized_payload: dict[str, Any] = Field(default_factory=dict)


def get_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return a LangChain-compatible JSON schema for a Pydantic model."""
    return model.model_json_schema()


INTERACTION_JSON_SCHEMA = get_json_schema(InteractionSchema)
LOG_INTERACTION_JSON_SCHEMA = get_json_schema(LogInteractionOutput)
EDIT_INTERACTION_JSON_SCHEMA = get_json_schema(EditInteractionOutput)
HCP_SEARCH_JSON_SCHEMA = get_json_schema(HcpSearchOutput)
MATERIAL_UPDATE_JSON_SCHEMA = get_json_schema(MaterialUpdateSchema)
FOLLOW_UP_UPDATE_JSON_SCHEMA = get_json_schema(FollowUpUpdateSchema)
VALIDATION_RESULT_JSON_SCHEMA = get_json_schema(PromptValidationResult)
