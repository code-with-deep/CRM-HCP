"""Draft-aware messaging helpers for planner clarifications and fallbacks."""

from __future__ import annotations

from app.langgraph.state import InteractionDraft


def draft_has_context(draft: InteractionDraft) -> bool:
    """Return True when the form already has an active interaction draft."""
    return bool(draft.hcp_name or draft.interaction_date or draft.topics_discussed)


def draft_subject_label(draft: InteractionDraft) -> str:
    """Return the HCP label for user-facing copy."""
    return draft.hcp_name or "the current HCP"


def draft_log_example(draft: InteractionDraft) -> str:
    """Example text for asking the user to log a visit first."""
    if draft.hcp_name:
        return (
            f'Continue updating the visit with {draft.hcp_name} — for example: '
            '"Follow up next Monday."'
        )
    return (
        'Describe the meeting first — for example: '
        '"I met Dr Deep today about stomach pain. Sentiment was neutral."'
    )


def draft_rate_limit_message(draft: InteractionDraft) -> str:
    """User-facing message when the LLM provider is temporarily unavailable."""
    if draft.hcp_name:
        return (
            "I'm briefly at capacity with the AI provider. "
            f"Your current draft is for {draft.hcp_name}. "
            'Try a short update like "Follow up next Monday" or '
            '"Update sentiment to neutral."'
        )
    return (
        "I'm briefly at capacity with the AI provider. "
        "Please try again in a few seconds with a short description of the HCP visit."
    )


def draft_retry_message(draft: InteractionDraft) -> str:
    """User-facing message when planning fails for a non-rate-limit reason."""
    if draft.hcp_name:
        return (
            f"I had trouble understanding that just now for {draft.hcp_name}. "
            "Please try a short follow-up update, such as "
            '"Follow up next Monday."'
        )
    return (
        "I had trouble understanding that just now. "
        "Please try again with a short description of the HCP interaction."
    )
