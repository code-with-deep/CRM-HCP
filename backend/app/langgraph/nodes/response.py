"""Response generator node."""

import json

from langchain_core.messages import AIMessage

from app.core.logging import get_logger
from app.langgraph.llm import LLMService, get_llm_service
from app.langgraph.memory import update_memory_after_turn
from app.langgraph.schemas import ResponseGeneratorOutput, ToolName
from app.langgraph.state import (
    AgentState,
    get_interaction_draft,
    serialize_response_output,
)
from app.prompts.prompt_loader import render_prompt

logger = get_logger(__name__)


def _build_fast_response(state: AgentState) -> str | None:
    """Build a concise template response when tool results are clear."""
    tool_result = state.get("tool_result") or {}
    selected_tool = state.get("selected_tool")
    draft = get_interaction_draft(state)
    patch = tool_result.get("interaction_patch") or {}
    validation_errors = state.get("validation_errors") or []

    if not tool_result.get("success", False) and selected_tool not in {None, "none"}:
        return tool_result.get("message") or (
            "I couldn't complete that update. Please try rephrasing the details."
        )

    if selected_tool == ToolName.LOG_INTERACTION.value:
        hcp = patch.get("hcp_name") or draft.hcp_name or "the HCP"
        topics = patch.get("topics_discussed") or draft.topics_discussed or []
        date_value = patch.get("interaction_date") or draft.interaction_date
        sentiment = patch.get("sentiment") or draft.sentiment
        parts = [f"I've logged your interaction with {hcp}"]
        if date_value:
            parts[0] += f" on {date_value}"
        parts[0] += "."
        if topics:
            parts.append(f"Topics captured: {', '.join(topics)}.")
        if sentiment:
            parts.append(f"Sentiment: {sentiment}.")
        if validation_errors:
            parts.append("Still needed: " + "; ".join(validation_errors))
        else:
            parts.append("You can continue adding details or save when ready.")
        return " ".join(parts)

    if selected_tool == ToolName.EDIT_INTERACTION.value:
        changed = list(patch.keys()) if isinstance(patch, dict) else []
        if "sentiment" in changed:
            sentiment = patch.get("sentiment") or draft.sentiment
            return f"I've updated the sentiment to {sentiment}."
        if "hcp_name" in changed:
            return f"I've updated the HCP name to {patch.get('hcp_name') or draft.hcp_name}."
        if "interaction_date" in changed or "interaction_time" in changed:
            date_value = patch.get("interaction_date") or draft.interaction_date
            time_value = patch.get("interaction_time") or draft.interaction_time
            parts = ["I've updated the interaction schedule"]
            if date_value:
                parts.append(f"date to {date_value}")
            if time_value:
                parts.append(f"time to {time_value}")
            return " and ".join(parts) + "."
        if changed:
            return f"I've updated {', '.join(changed)} in the interaction draft."
        return "I've applied your edit to the interaction draft."

    if selected_tool == ToolName.SEARCH_HCP.value:
        hcp_context = tool_result.get("hcp_context") or state.get("current_hcp") or {}
        name = hcp_context.get("name")
        if name:
            hospital = hcp_context.get("hospital")
            city = hcp_context.get("city")
            location = ", ".join(part for part in [hospital, city] if part)
            suffix = f" ({location})" if location else ""
            return f"I found {name}{suffix} and updated the HCP context."
        return tool_result.get("message") or "I couldn't find a matching HCP."

    if selected_tool == ToolName.MATERIALS_AND_SAMPLES.value:
        materials = patch.get("materials_shared") or draft.materials_shared or []
        samples = patch.get("samples_distributed") or draft.samples_distributed or []
        bits = []
        if materials:
            bits.append(f"materials: {', '.join(materials)}")
        if samples:
            bits.append(f"samples: {', '.join(samples)}")
        if bits:
            return f"I've updated {' and '.join(bits)}."
        return "I've updated the materials and samples section."

    if selected_tool == ToolName.OUTCOME_AND_FOLLOWUP.value:
        follow_up = patch.get("follow_up_actions") or draft.follow_up_actions
        outcomes = patch.get("outcomes") or draft.outcomes
        hcp = draft.hcp_name or "the HCP"
        if follow_up and not outcomes:
            return f"I've updated the follow-up for {hcp}: {follow_up}"
        if outcomes and not follow_up:
            return f"I've captured the outcome for {hcp}: {outcomes}"
        bits = []
        if outcomes:
            bits.append("outcomes")
        if follow_up:
            bits.append("follow-up actions")
        if patch.get("sentiment") or draft.sentiment:
            bits.append("sentiment")
        if bits:
            return f"I've updated the {', '.join(bits)}."
        return "I've updated the outcome and follow-up details."

    # Conversational / no-tool turns: prefer planner clarification over another LLM call.
    intent = state.get("intent_output") or {}
    planner = state.get("planner_output") or {}
    clarification = intent.get("clarification_question") or planner.get("clarification_question")
    if clarification:
        return clarification

    # For general assistance with no active draft, provide a short guided prompt.
    primary_intent = intent.get("primary_intent") or planner.get("primary_intent") or ""
    if primary_intent == "general_assistance":
        if draft.hcp_name:
            return (
                f"I'm ready to help with your interaction with {draft.hcp_name}. "
                "Just tell me what you'd like to update — sentiment, follow-up, materials, or outcomes."
            )
        return (
            "To get started, describe an HCP interaction — for example: "
            "\"I met Dr Sharma today to discuss CardioMax efficacy.\" "
            "I'll capture it in the form on the left."
        )

    return None


async def response_generator_node(
    state: AgentState,
    llm_service: LLMService | None = None,
) -> dict:
    """Generate the final enterprise CRM assistant response."""
    draft = get_interaction_draft(state)
    intent_output = state.get("intent_output") or {}

    # Prefer confirming captured data over asking for already-provided fields.
    fast_message = _build_fast_response(state)
    if fast_message:
        response_output = ResponseGeneratorOutput(
            message=fast_message,
        )
        return {
            "response": fast_message,
            "response_output": serialize_response_output(response_output),
            "messages": [AIMessage(content=fast_message)],
            "memory": update_memory_after_turn(
                state=state,
                assistant_response=fast_message,
                selected_tool=state.get("selected_tool"),
                updated_draft=draft,
            ),
            "error_message": None,
        }

    if intent_output.get("requires_clarification") and intent_output.get("clarification_question"):
        clarification = intent_output["clarification_question"]
        return {
            "response": clarification,
            "response_output": ResponseGeneratorOutput(
                message=clarification,
            ).model_dump(mode="json"),
            "messages": [AIMessage(content=clarification)],
            "memory": update_memory_after_turn(
                state=state,
                assistant_response=clarification,
                selected_tool=state.get("selected_tool"),
                updated_draft=draft,
            ),
        }

    service = llm_service or get_llm_service()
    prompt = render_prompt(
        "response",
        planner_output=json.dumps(state.get("planner_output") or {}, ensure_ascii=True),
        intent_output=json.dumps(intent_output, ensure_ascii=True),
        router_output=json.dumps(state.get("router_output") or {}, ensure_ascii=True),
        validation_output=json.dumps(state.get("validation_output") or {}, ensure_ascii=True),
        interaction_draft=json.dumps(draft.to_serializable(), ensure_ascii=True),
        error_context=state.get("error_message") or "none",
    )

    try:
        response_output = await service.ainvoke_structured(
            schema=ResponseGeneratorOutput,
            node_prompt=prompt,
            user_content=json.dumps(
                {
                    "latest_user_message": state.get("memory", {}).get("last_user_message"),
                    "selected_tool": state.get("selected_tool"),
                    "tool_result": state.get("tool_result"),
                },
                ensure_ascii=True,
            ),
        )
        message = response_output.message
    except Exception as exc:
        logger.error("Response generator failed: %s", str(exc), exc_info=exc)
        message = (
            "I'm briefly busy right now. Please try again in a few seconds, "
            "or ask \"how can you help me\" for examples of what I can update."
        )
        response_output = ResponseGeneratorOutput(message=message)

    return {
        "response": message,
        "response_output": serialize_response_output(response_output),
        "messages": [AIMessage(content=message)],
        "memory": update_memory_after_turn(
            state=state,
            assistant_response=message,
            selected_tool=state.get("selected_tool"),
            updated_draft=draft,
        ),
        "error_message": None,
    }
