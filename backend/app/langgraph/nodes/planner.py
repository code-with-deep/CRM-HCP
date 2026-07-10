"""Planner node for LangGraph agent."""

import json

from app.core.logging import get_logger
from app.langgraph.draft_messages import draft_log_example, draft_rate_limit_message, draft_retry_message
from app.langgraph.llm import LLMService, get_llm_service
from app.langgraph.local_planner import plan_from_local_rules
from app.langgraph.memory import build_memory_summary, serialize_messages_for_prompt
from app.prompts.prompt_loader import render_prompt
from app.langgraph.schemas import AgentIntent, PlannerOutput, ToolName
from app.langgraph.state import (
    AgentState,
    get_hcp_context,
    get_interaction_draft,
    get_user_context,
    serialize_planner_output,
)

logger = get_logger(__name__)


def _last_user_text(state: AgentState) -> str:
    """Return the latest user message text from state.

    Prefer the newest HumanMessage so we never plan against a stale memory value.
    """
    for message in reversed(state.get("messages") or []):
        role = getattr(message, "type", None) or getattr(message, "role", None)
        content = getattr(message, "content", None)
        if role in {"human", "user"} and isinstance(content, str) and content.strip():
            return content.strip()

    memory = state.get("memory") or {}
    last_user = memory.get("last_user_message")
    if isinstance(last_user, str) and last_user.strip():
        return last_user.strip()
    return ""


def _enrich_planner_with_draft_guards(
    planner_output: PlannerOutput,
    state: AgentState,
) -> PlannerOutput:
    """Block premature edits when no interaction draft exists yet."""
    draft = get_interaction_draft(state)
    has_base = bool(draft.hcp_name or draft.interaction_date or draft.topics_discussed)
    if has_base:
        return planner_output

    edit_tools = {
        ToolName.EDIT_INTERACTION,
        ToolName.MATERIALS_AND_SAMPLES,
        ToolName.OUTCOME_AND_FOLLOWUP,
    }
    if planner_output.selected_tool not in edit_tools:
        return planner_output

    return PlannerOutput(
        objective="Ask the user to log the interaction before editing fields.",
        requires_tool_execution=False,
        context_summary="No base interaction draft is present.",
        primary_intent=AgentIntent.GENERAL_ASSISTANCE,
        confidence=0.95,
        reasoning="Edit requested before an interaction was logged.",
        requires_clarification=True,
        clarification_question=(
            "I don't have an interaction on the form yet, so I can't update that detail. "
            f"Please describe the meeting first. {draft_log_example(draft)} "
            "After that, I can change follow-up, sentiment, materials, or other fields."
        ),
        selected_tool=ToolName.NONE,
        should_execute_tool=False,
        routing_reasoning="Draft-aware guard prevented premature edit.",
    )


async def planner_node(
    state: AgentState,
    llm_service: LLMService | None = None,
) -> dict:
    """Understand the user request and produce an execution plan without running tools."""
    service = llm_service or get_llm_service()
    draft = get_interaction_draft(state)
    hcp_context = get_hcp_context(state)
    user_context = get_user_context(state)
    last_user = _last_user_text(state)

    # High-confidence CRM intents: resolve locally to keep demos reliable and save tokens.
    local_plan = plan_from_local_rules(state, last_user) if last_user else None
    if local_plan is not None and local_plan.confidence >= 0.9:
        guarded = _enrich_planner_with_draft_guards(local_plan, state)
        logger.info(
            "Planner used local high-confidence plan intent=%s tool=%s",
            guarded.primary_intent.value,
            guarded.selected_tool.value,
        )
        return {
            "planner_output": serialize_planner_output(guarded),
            "error_message": None,
        }

    prompt = render_prompt(
        "planner",
        interaction_draft=json.dumps(draft.to_serializable(), ensure_ascii=True),
        hcp_context=json.dumps(hcp_context.to_serializable() if hcp_context else {}, ensure_ascii=True),
        memory_summary=build_memory_summary(state),
        user_context=json.dumps(user_context.to_serializable(), ensure_ascii=True),
    )

    try:
        planner_output = await service.ainvoke_structured(
            schema=PlannerOutput,
            node_prompt=prompt,
            user_content=serialize_messages_for_prompt(state.get("messages", [])),
        )
        guarded = _enrich_planner_with_draft_guards(planner_output, state)
        return {
            "planner_output": serialize_planner_output(guarded),
            "error_message": None,
        }
    except Exception as exc:
        logger.error("Planner node failed: %s", str(exc), exc_info=exc)
        recovered = plan_from_local_rules(state, last_user) if last_user else None
        if recovered is not None:
            guarded = _enrich_planner_with_draft_guards(recovered, state)
            logger.warning(
                "Planner recovered via local rules after LLM failure: %s",
                guarded.objective,
            )
            return {
                "planner_output": serialize_planner_output(guarded),
                "error_message": None,
            }

        is_rate_limited = "rate" in str(exc).lower() or "429" in str(exc)
        draft = get_interaction_draft(state)
        return {
            "planner_output": PlannerOutput(
                objective="Handle the user request with a safe conversational response.",
                requires_tool_execution=False,
                context_summary="Planner failed due to an LLM error.",
                constraints=["llm_failure"],
                primary_intent=AgentIntent.GENERAL_ASSISTANCE,
                requires_clarification=True,
                clarification_question=(
                    draft_rate_limit_message(draft)
                    if is_rate_limited
                    else draft_retry_message(draft)
                ),
                selected_tool=ToolName.NONE,
                should_execute_tool=False,
            ).model_dump(mode="json"),
            "error_message": f"Planner node failed: {exc}",
        }
