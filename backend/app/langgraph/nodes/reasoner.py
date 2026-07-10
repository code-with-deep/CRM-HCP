"""Intent reasoner node for LangGraph agent."""

from app.core.logging import get_logger
from app.langgraph.schemas import AgentIntent, IntentReasonerOutput
from app.langgraph.state import AgentState, serialize_intent_output

logger = get_logger(__name__)


async def intent_reasoner_node(state: AgentState) -> dict:
    """Derive intent from planner orchestration output (no extra LLM call)."""
    planner_output = state.get("planner_output") or {}

    try:
        primary_raw = planner_output.get("primary_intent") or AgentIntent.UNKNOWN.value
        try:
            primary_intent = AgentIntent(primary_raw)
        except ValueError:
            primary_intent = AgentIntent.UNKNOWN

        secondary: list[AgentIntent] = []
        for item in planner_output.get("secondary_intents") or []:
            try:
                secondary.append(AgentIntent(item))
            except ValueError:
                continue

        confidence = float(planner_output.get("confidence") or 0.5)
        confidence = max(0.0, min(1.0, confidence))

        intent_output = IntentReasonerOutput(
            primary_intent=primary_intent,
            secondary_intents=secondary,
            confidence=confidence,
            reasoning=planner_output.get("reasoning")
            or planner_output.get("context_summary")
            or "Derived from planner orchestration.",
            requires_clarification=bool(planner_output.get("requires_clarification", False)),
            clarification_question=planner_output.get("clarification_question"),
        )
        logger.info(
            "Intent derived from planner primary_intent=%s confidence=%.2f",
            intent_output.primary_intent.value,
            intent_output.confidence,
        )
        return {
            "intent_output": serialize_intent_output(intent_output),
            "error_message": None,
        }
    except Exception as exc:
        logger.error("Intent reasoner node failed: %s", str(exc), exc_info=exc)
        return {
            "intent_output": IntentReasonerOutput(
                primary_intent=AgentIntent.UNKNOWN,
                confidence=0.0,
                reasoning="Intent derivation failed.",
                requires_clarification=True,
                clarification_question=(
                    "I encountered a temporary issue understanding your request. "
                    "Could you please rephrase what you would like to update?"
                ),
            ).model_dump(mode="json"),
            "error_message": f"Intent reasoner node failed: {exc}",
        }
