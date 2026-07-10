"""OutcomeAndFollowupTool implementation."""

from typing import Any

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState, get_interaction_draft
from app.langgraph.tools.base_tool import BaseCrmTool
from app.langgraph.tools.date_utils import normalize_interaction_patch
from app.langgraph.tools.dependencies import ToolDependencies
from app.langgraph.tools.schemas import OutcomeAndFollowupToolInput, ToolExecutionResult
from app.prompts.schemas import FollowUpUpdateSchema

logger = get_logger(__name__)

_HINT_FIELDS = ("outcomes", "follow_up_actions", "sentiment", "additional_notes")


class OutcomeAndFollowupTool(BaseCrmTool):
    """Extract outcomes, follow-up actions, reminders, sentiment, and next steps."""

    name = ToolName.OUTCOME_AND_FOLLOWUP
    description = (
        "Understand meeting outcomes, doctor feedback, sentiment, future commitments, "
        "requested information, and follow-up schedules then update the interaction draft."
    )
    input_schema = OutcomeAndFollowupToolInput
    output_schema = FollowUpUpdateSchema
    prompt_name = "outcome_and_followup"

    async def execute(
        self,
        *,
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        """Update outcomes, follow-up, and sentiment fields in the interaction draft."""
        try:
            validated_input = self.input_schema.model_validate(tool_input)
            user_instruction = validated_input.user_instruction or self.build_user_instruction(
                state,
                tool_input,
            )
            current_draft = get_interaction_draft(state)
            router_hints = normalize_interaction_patch(
                self._extract_router_hints(validated_input),
            )

            # Fast path: planner already extracted outcomes/sentiment/follow-up.
            if router_hints:
                logger.info(
                    "OutcomeAndFollowupTool using planner hints (skip LLM): %s",
                    list(router_hints.keys()),
                )
                return self.success(
                    self.name,
                    "Outcomes and follow-up details updated in the interaction draft.",
                    interaction_patch=router_hints,
                    metadata={
                        "fields_updated": list(router_hints.keys()),
                        "source": "planner_hints",
                    },
                )

            llm_output = await self.invoke_structured_llm(
                dependencies=dependencies,
                output_schema=FollowUpUpdateSchema,
                prompt_name=self.prompt_name,
                prompt_kwargs={
                    "conversation_history": self.serialize_history(state),
                    "current_interaction": self.current_draft_json(state),
                    "user_instruction": user_instruction,
                },
                user_content=user_instruction,
            )

            interaction_patch: dict[str, Any] = {}

            if llm_output.outcomes is not None:
                interaction_patch["outcomes"] = llm_output.outcomes

            follow_up_parts: list[str] = []
            if current_draft.follow_up_actions:
                follow_up_parts.append(current_draft.follow_up_actions)
            if llm_output.follow_up_actions:
                follow_up_parts.append(llm_output.follow_up_actions)
            if llm_output.reminder:
                follow_up_parts.append(f"Reminder: {llm_output.reminder}")
            if llm_output.follow_up_date:
                follow_up_parts.append(f"Follow-up date: {llm_output.follow_up_date}")
            if llm_output.suggested_follow_up_summary:
                follow_up_parts.append(llm_output.suggested_follow_up_summary)

            if follow_up_parts:
                interaction_patch["follow_up_actions"] = "\n".join(
                    dict.fromkeys(part for part in follow_up_parts if part),
                )

            # Apply sentiment if the schema exposes it; otherwise rely on planner hints.
            sentiment = getattr(llm_output, "sentiment", None)
            if isinstance(sentiment, str) and sentiment.strip():
                interaction_patch["sentiment"] = sentiment

            interaction_patch = normalize_interaction_patch(interaction_patch)

            if not interaction_patch:
                return self.failure(
                    self.name,
                    "No outcomes, sentiment, or follow-up details were identified in the request.",
                )

            return self.success(
                self.name,
                "Outcomes and follow-up details updated in the interaction draft.",
                interaction_patch=interaction_patch,
                metadata={
                    "followup_update": llm_output.model_dump(mode="json"),
                },
            )
        except RuntimeError as exc:
            logger.error("OutcomeAndFollowupTool LLM failure: %s", str(exc), exc_info=exc)
            return self.failure(
                self.name,
                "I could not extract outcomes or follow-up details right now.",
            )
        except Exception as exc:
            logger.error("OutcomeAndFollowupTool failed: %s", str(exc), exc_info=exc)
            return self.failure(
                self.name,
                "I could not update outcomes or follow-up right now. Please try again in a moment.",
            )

    @staticmethod
    def _extract_router_hints(validated_input: OutcomeAndFollowupToolInput) -> dict[str, Any]:
        """Collect optional outcome/sentiment hints from the planner/router."""
        payload = validated_input.model_dump()
        hints: dict[str, Any] = {}
        for field_name in _HINT_FIELDS:
            value = payload.get(field_name)
            if value in (None, "", []):
                continue
            hints[field_name] = value
        return hints


outcome_and_followup_tool = OutcomeAndFollowupTool()
