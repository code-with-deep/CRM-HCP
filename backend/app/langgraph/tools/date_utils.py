"""Date and relative-time helpers for CRM interaction extraction."""

from __future__ import annotations

from datetime import date, timedelta
import re


_RELATIVE_DATE_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"^today$", re.IGNORECASE), 0),
    (re.compile(r"^tonight$", re.IGNORECASE), 0),
    (re.compile(r"^yesterday$", re.IGNORECASE), -1),
    (re.compile(r"^tomorrow$", re.IGNORECASE), 1),
]


def resolve_relative_date(value: str | None, *, reference: date | None = None) -> str | None:
    """Normalize relative date phrases to ISO YYYY-MM-DD."""
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    # Already ISO.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned):
        return cleaned

    today = reference or date.today()
    for pattern, offset in _RELATIVE_DATE_PATTERNS:
        if pattern.fullmatch(cleaned):
            return (today + timedelta(days=offset)).isoformat()

    # Phrases like "today morning" / "met today"
    lowered = cleaned.lower()
    if "today" in lowered:
        return today.isoformat()
    if "yesterday" in lowered:
        return (today - timedelta(days=1)).isoformat()
    if "tomorrow" in lowered:
        return (today + timedelta(days=1)).isoformat()

    return cleaned


def normalize_interaction_patch(
    patch: dict,
    *,
    reference: date | None = None,
) -> dict:
    """Normalize common extracted values in an interaction patch."""
    if not patch:
        return patch

    normalized = dict(patch)
    if "interaction_date" in normalized:
        normalized["interaction_date"] = resolve_relative_date(
            normalized.get("interaction_date"),
            reference=reference,
        )

    sentiment = normalized.get("sentiment")
    if isinstance(sentiment, str):
        sentiment_value = sentiment.strip().lower()
        if sentiment_value in {"positive", "neutral", "negative"}:
            normalized["sentiment"] = sentiment_value
        else:
            normalized.pop("sentiment", None)

    return normalized
