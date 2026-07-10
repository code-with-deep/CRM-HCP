"""Deterministic topic extraction helpers for natural-language CRM logging."""

from __future__ import annotations

import re

_TOPIC_STOPWORDS = {
    "a",
    "an",
    "the",
    "with",
    "at",
    "on",
    "for",
    "to",
    "of",
    "in",
    "about",
    "abou",
    "today",
    "yesterday",
    "tomorrow",
    "sentiment",
    "was",
    "were",
    "is",
    "are",
}

_TOPIC_TYPOS = {
    "dentail": "dental",
    "teet": "teeth",
    "abou": "about",
    "muscels": "muscles",
}

_DISCUSS_TOPIC_RE = re.compile(
    r"(?:discuss(?:ed)?|talk(?:ed)?|spoke)\s+(?:about\s+)?(.+?)(?:\.|$|sentiment|shared|follow)",
    re.IGNORECASE,
)
_STANDALONE_ABOUT_RE = re.compile(
    r"(?:about|abou|regarding)\s+(?:the\s+)?(.+?)(?:\.|$|sentiment|shared|follow)",
    re.IGNORECASE,
)
_AFTER_HCP_RE = re.compile(
    r"\bdr\.?\s+[A-Za-z]+(?:\s+[A-Za-z]+)?\s+"
    r"(?:today\s+)?(?:about|abou|regarding|on)\s+(?:the\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)


def normalize_topic_phrase(phrase: str) -> str:
    """Normalize common typos and trim filler words from a topic phrase."""
    cleaned = phrase.strip(" .,;:")
    if not cleaned:
        return ""

    words: list[str] = []
    for raw_word in cleaned.split():
        token = raw_word.lower().strip(".,;:")
        if token in _TOPIC_STOPWORDS:
            continue
        if token in _TOPIC_TYPOS:
            words.append(_TOPIC_TYPOS[token])
            continue
        words.append(raw_word)

    result = " ".join(words).strip()
    if not result:
        return ""

    if result.endswith(" issue"):
        result = f"{result}s"

    return result[0].upper() + result[1:] if len(result) > 1 else result.upper()


def extract_topics_from_message(text: str) -> list[str]:
    """Extract discussion topics from a free-form interaction message."""
    if not text or not text.strip():
        return []

    for pattern in (_DISCUSS_TOPIC_RE, _STANDALONE_ABOUT_RE, _AFTER_HCP_RE):
        match = pattern.search(text)
        if not match:
            continue
        topic = normalize_topic_phrase(match.group(1))
        if topic:
            return [topic]

    # Fallback: capture clinical issue phrases when no "about" preposition is present.
    issue_match = re.search(
        r"\b((?:dental|dentail|teeth|teet|oral|orthodont\w*|gum|gums)[\w\s,-]*"
        r"(?:issue|issues|problem|concern)s?)\b",
        text,
        re.IGNORECASE,
    )
    if issue_match:
        topic = normalize_topic_phrase(issue_match.group(1))
        if topic:
            return [topic]

    return []
