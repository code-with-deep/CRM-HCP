"""Tests for draft-aware continuation planning."""

from app.langgraph.local_planner import plan_from_local_rules
from app.langgraph.state import InteractionDraft, create_initial_state


def test_continuation_follow_up_uses_current_draft_doctor() -> None:
    draft = InteractionDraft(
        hcp_name="Dr Deep",
        interaction_date="2026-07-10",
        topics_discussed=["Stomach pain"],
    )
    state = create_initial_state(
        user_message="he told me to meet agin on next monday",
        current_interaction=draft,
    )

    plan = plan_from_local_rules(state, "he told me to meet agin on next monday")

    assert plan is not None
    assert plan.selected_tool.value == "outcome_and_followup"
    assert plan.tool_input is not None
    assert "Dr Deep" in (plan.tool_input.follow_up_actions or "")
    assert "Monday" in (plan.tool_input.follow_up_actions or "")


def test_new_doctor_message_starts_fresh_log_not_continuation() -> None:
    draft = InteractionDraft(
        hcp_name="Dr Aman",
        interaction_date="2026-07-10",
        topics_discussed=["Dental issues"],
    )
    state = create_initial_state(
        user_message="i meet Dr. Deep regarding stomach pain",
        current_interaction=draft,
    )

    plan = plan_from_local_rules(state, "i meet Dr. Deep regarding stomach pain")

    assert plan is not None
    assert plan.selected_tool.value == "log_interaction"
    assert plan.tool_input is not None
    assert plan.tool_input.hcp_name == "Dr Deep"
