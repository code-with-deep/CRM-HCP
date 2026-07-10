"""Tests for state updater draft replacement on new logs."""

from app.langgraph.nodes.updater import _merge_interaction_patch, _replace_interaction_draft
from app.langgraph.state import InteractionDraft


def test_replace_interaction_draft_drops_stale_topics() -> None:
    patch = {
        "hcp_name": "Dr Aman",
        "interaction_date": "2026-07-10",
        "interaction_type": "Meeting",
        "topics_discussed": ["Dental and teeth issues"],
    }

    draft = _replace_interaction_draft(patch)

    assert draft.hcp_name == "Dr Aman"
    assert draft.topics_discussed == ["Dental and teeth issues"]
    assert draft.sentiment is None
    assert draft.materials_shared == []


def test_merge_interaction_patch_preserves_existing_topics_for_edits() -> None:
    current = InteractionDraft(
        hcp_name="Dr Aman",
        interaction_date="2026-07-10",
        topics_discussed=["Dental and teeth issues"],
    )
    merged = _merge_interaction_patch(
        current,
        {"follow_up_actions": "Follow up next Friday."},
    )

    assert merged.topics_discussed == ["Dental and teeth issues"]
    assert merged.follow_up_actions == "Follow up next Friday."
