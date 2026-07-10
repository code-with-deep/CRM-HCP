"""EditInteractionTool implementation."""

from typing import Any

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState, get_interaction_draft
from app.langgraph.tools.base_tool import BaseCrmTool
from app.langgraph.tools.date_utils import normalize_interaction_patch
from app.langgraph.tools.dependencies import ToolDependencies
from app.langgraph.tools.schemas import EditInteractionToolInput, ToolExecutionResult
from app.prompts.schemas import EditInteractionOutput

logger = get_logger(__name__)

_HINT_FIELDS = (
    "hcp_name",
    "interaction_type",
    "interaction_date",
    "interaction_time",
    "attendees",
    "topics_discussed",
    "materials_shared",
    "samples_distributed",
    "sentiment",
    "outcomes",
    "follow_up_actions",
    "additional_notes",
)


class EditInteractionTool(BaseCrmTool):
    """Surgically update fields in the current interaction draft."""

    name = ToolName.EDIT_INTERACTION
    description = (
        "Update only the explicitly requested fields in the current interaction draft while "
        "preserving all unchanged values."
    )
    input_schema = EditInteractionToolInput
    output_schema = EditInteractionOutput
    prompt_name = "edit_interaction"

    async def execute(
        self,
        *,
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        """Apply surgical edits to the current interaction draft."""
        try:
            validated_input = self.input_schema.model_validate(tool_input)
            current_draft = get_interaction_draft(state)
            router_hints = normalize_interaction_patch(
                self._extract_router_hints(validated_input),
            )
            user_instruction = validated_input.user_instruction or self.build_user_instruction(
                state,
                tool_input,
            )

            # Fast path: planner already extracted the fields to change.
            if router_hints:
                logger.info(
                    "EditInteractionTool using planner hints (skip LLM): %s",
                    list(router_hints.keys()),
                )
                return self.success(
                    self.name,
                    "Interaction draft updated.",
                    interaction_patch=router_hints,
                    metadata={
                        "fields_updated": list(router_hints.keys()),
                        "source": "planner_hints",
                    },
                )

            llm_output = await self.invoke_structured_llm(
                dependencies=dependencies,
                output_schema=EditInteractionOutput,
                prompt_name=self.prompt_name,
                prompt_kwargs={
                    "current_interaction": self.current_draft_json(state),
                    "conversation_history": self.serialize_history(state),
                    "user_instruction": user_instruction,
                },
                user_content=user_instruction,
            )

            interaction_patch = self.diff_interaction_drafts(
                current_draft,
                self.map_interaction_schema_to_patch(llm_output),
                fields_updated=llm_output.fields_updated or None,
            )

            if not interaction_patch and llm_output.fields_updated:
                interaction_patch = self.diff_interaction_drafts(
                    current_draft,
                    self.map_interaction_schema_to_patch(llm_output),
                    fields_updated=llm_output.fields_updated,
                )

            updated_payload = self.map_interaction_schema_to_patch(llm_output)
            interaction_patch = normalize_interaction_patch(interaction_patch)

            if not interaction_patch:
                return self.failure(
                    self.name,
                    "No interaction fields were updated. Please specify what should change.",
                    metadata={"updated_interaction": updated_payload},
                )

            logger.info("EditInteractionTool updated fields: %s", list(interaction_patch.keys()))

            return self.success(
                self.name,
                "Interaction draft updated.",
                interaction_patch=interaction_patch,
                metadata={
                    "fields_updated": llm_output.fields_updated,
                    "updated_interaction": updated_payload,
                },
            )
        except RuntimeError as exc:
            logger.error("EditInteractionTool LLM failure: %s", str(exc), exc_info=exc)
            return self.failure(self.name, "I could not apply the requested edits right now.")
        except Exception as exc:
            logger.error("EditInteractionTool failed: %s", str(exc), exc_info=exc)
            return self.failure(
                self.name,
                "I could not apply the requested edits right now. Please try again in a moment.",
            )

    @staticmethod
    def _extract_router_hints(validated_input: EditInteractionToolInput) -> dict[str, Any]:
        """Collect optional edit hints provided by the planner/router."""
        payload = validated_input.model_dump()
        hints: dict[str, Any] = {}
        for field_name in _HINT_FIELDS:
            value = payload.get(field_name)
            if value in (None, "", []):
                continue
            hints[field_name] = value
        return hints


edit_interaction_tool = EditInteractionTool()
