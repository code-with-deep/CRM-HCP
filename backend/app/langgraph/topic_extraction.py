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
    "him",
    "her",
    "their",
    "its",
    "this",
    "that",
    "which",
    "he",
    "she",
    "they",
    "i",
    "we",
    "me",
    "my",
    "our",
    "very",
    "quite",
    "really",
}

_TOPIC_TYPOS = {
    # existing
    "dentail": "dental",
    "teet": "teeth",
    "abou": "about",
    "muscels": "muscles",
    # expanded pharmaceutical / clinical typos
    "eficacy": "efficacy",
    "eficiency": "efficiency",
    "presciption": "prescription",
    "prescribtion": "prescription",
    "dosege": "dosage",
    "dosege": "dosage",
    "mediaction": "medication",
    "medicaton": "medication",
    "treatement": "treatment",
    "treament": "treatment",
    "clincal": "clinical",
    "clinicl": "clinical",
    "theraputic": "therapeutic",
    "therepeutic": "therapeutic",
    "cardivascular": "cardiovascular",
    "cardiovasculer": "cardiovascular",
    "hypertenshun": "hypertension",
    "hypertensoin": "hypertension",
    "diabeties": "diabetes",
    "diabetis": "diabetes",
    "oncololgy": "oncology",
    "oncolgy": "oncology",
    "neurolgoy": "neurology",
    "neurologoy": "neurology",
    "gynaecolgoy": "gynaecology",
    "orthopaedics": "orthopaedics",
    "paedatrics": "paediatrics",
    "pharamacy": "pharmacy",
    "pharmcy": "pharmacy",
    "saftey": "safety",
    "safeity": "safety",
    "complient": "compliance",
    "complianse": "compliance",
    "guidlines": "guidelines",
    "guidelins": "guidelines",
    "managment": "management",
    "managemnt": "management",
    "reserch": "research",
    "reseach": "research",
    "trieal": "trial",
    "traial": "trial",
    "benefites": "benefits",
    "benifits": "benefits",
    "sideeffects": "side effects",
    "side-effects": "side effects",
    "adverse-effects": "adverse effects",
    "co-morbidity": "comorbidity",
}

# --- Primary extraction patterns ---
_DISCUSS_TOPIC_RE = re.compile(
    r"(?:discuss(?:ed|ing)?|talk(?:ed|ing)?|spoke|speak|spoken|chat(?:ted)?)"
    r"(?:\s+(?:to|with|about))?\s+(?:the\s+)?(.+?)"
    r"(?:\.|$|sentiment|shared|follow|and\s+also|\bwith\b|\bto\b)",
    re.IGNORECASE,
)

_STANDALONE_ABOUT_RE = re.compile(
    r"(?:about|abou|regarding|concerning|re:)\s+(?:the\s+)?(.+?)"
    r"(?:\.|$|sentiment|shared|follow|,\s+(?:and\s+)?(?:he|she|they|the\s+doctor))",
    re.IGNORECASE,
)

_AFTER_HCP_RE = re.compile(
    r"\bdr\.?\s+[A-Za-z]+(?:\s+[A-Za-z]+)?\s+"
    r"(?:today\s+)?(?:about|abou|regarding|on|for)\s+(?:the\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)

# New patterns
_FOR_TOPIC_RE = re.compile(
    r"(?:for\s+(?:a\s+)?(?:discussion|review|talk|meeting|call)\s+(?:on|about|of|regarding))\s+(?:the\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)

_ON_TOPIC_RE = re.compile(
    r"(?:on\s+the\s+topic\s+of|on\s+topics?\s+(?:of|including|such\s+as))\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)

_TOPIC_LIST_SPLITTER_RE = re.compile(
    # Split on:  ", and",  ", ",  "; ",  " as well as ",  " plus "
    # Do NOT split on plain " and " alone — that breaks compound phrases like
    # "dental and teeth issues" or "cardiovascular and hypertension".
    r"\s*(?:,\s*(?:and\s+)?|;\s*|\s+as\s+well\s+as\s+|\s+plus\s+)\s*",
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


def _split_topic_list(raw: str) -> list[str]:
    """Split a raw topic string on commas, semicolons, and conjunctions."""
    parts = _TOPIC_LIST_SPLITTER_RE.split(raw)
    return [p.strip() for p in parts if p.strip()]


def extract_topics_from_message(text: str) -> list[str]:
    """Extract ALL discussion topics from a free-form interaction message.

    Supports multiple topics separated by commas, 'and', 'as well as', etc.
    Returns a deduplicated list ordered by appearance.
    """
    if not text or not text.strip():
        return []

    seen: set[str] = set()
    topics: list[str] = []

    def _add(raw: str) -> None:
        for part in _split_topic_list(raw):
            normalized = normalize_topic_phrase(part)
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                topics.append(normalized)

    # Try every pattern and accumulate all matches
    for pattern in (
        _DISCUSS_TOPIC_RE,
        _STANDALONE_ABOUT_RE,
        _AFTER_HCP_RE,
        _FOR_TOPIC_RE,
        _ON_TOPIC_RE,
    ):
        for match in pattern.finditer(text):
            _add(match.group(1))

    if topics:
        return topics

    # Fallback: capture clinical issue phrases when no "about" preposition is present.
    issue_match = re.search(
        r"\b((?:dental|dentail|teeth|teet|oral|orthodont\w*|gum|gums)[\w\s,-]*"
        r"(?:issue|issues|problem|concern)s?)\b",
        text,
        re.IGNORECASE,
    )
    if issue_match:
        _add(issue_match.group(1))

    return topics
