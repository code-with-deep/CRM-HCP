"""Tests for deterministic topic extraction."""

from app.langgraph.topic_extraction import extract_topics_from_message, normalize_topic_phrase


def test_extract_topics_from_about_typo() -> None:
    topics = extract_topics_from_message(
        "i meet Dr. Aman abou the dentail and teet issue",
    )
    assert topics == ["Dental and teeth issues"]


def test_extract_topics_from_discussed_phrase() -> None:
    topics = extract_topics_from_message(
        "I met Dr Sharma today to discuss CardioMax efficacy.",
    )
    assert topics == ["CardioMax efficacy"]


def test_normalize_topic_phrase_fixes_common_typos() -> None:
    assert normalize_topic_phrase("dentail and teet issue") == "Dental and teeth issues"
