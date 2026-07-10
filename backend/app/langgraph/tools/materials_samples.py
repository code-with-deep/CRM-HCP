"""MaterialsAndSamplesTool implementation."""

from typing import Any

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState, get_interaction_draft
from app.langgraph.tools.base_tool import BaseCrmTool
from app.langgraph.tools.dependencies import ToolDependencies
from app.langgraph.tools.schemas import MaterialsAndSamplesToolInput, ToolExecutionResult
from app.prompts.schemas import MaterialUpdateSchema

logger = get_logger(__name__)


class MaterialsAndSamplesTool(BaseCrmTool):
    """Extract and update materials shared and samples distributed."""

    name = ToolName.MATERIALS_AND_SAMPLES
    description = (
        "Extract brochures, leaflets, presentations, clinical studies, and sample packs "
        "with quantities from the conversation and update the interaction draft."
    )
    input_schema = MaterialsAndSamplesToolInput
    output_schema = MaterialUpdateSchema
    prompt_name = "materials_and_samples"

    async def execute(
        self,
        *,
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        """Update materials and samples in the interaction draft."""
        try:
            validated_input = self.input_schema.model_validate(tool_input)
            user_instruction = validated_input.user_instruction or self.build_user_instruction(
                state,
                tool_input,
            )
            current_draft = get_interaction_draft(state)

            hint_materials = list(validated_input.materials_shared or [])
            hint_samples = list(validated_input.samples_distributed or [])
            if hint_materials or hint_samples:
                interaction_patch: dict[str, Any] = {}
                if hint_materials:
                    interaction_patch["materials_shared"] = self._merge_list_values(
                        current_draft.materials_shared,
                        hint_materials,
                    )
                if hint_samples:
                    interaction_patch["samples_distributed"] = self._merge_list_values(
                        current_draft.samples_distributed,
                        hint_samples,
                    )
                logger.info(
                    "MaterialsAndSamplesTool using planner hints (skip LLM): %s",
                    list(interaction_patch.keys()),
                )
                return self.success(
                    self.name,
                    "Materials and samples updated in the interaction draft.",
                    interaction_patch=interaction_patch,
                    metadata={"source": "planner_hints", "fields_updated": list(interaction_patch.keys())},
                )

            llm_output = await self.invoke_structured_llm(
                dependencies=dependencies,
                output_schema=MaterialUpdateSchema,
                prompt_name=self.prompt_name,
                prompt_kwargs={
                    "conversation_history": self.serialize_history(state),
                    "current_interaction": self.current_draft_json(state),
                    "user_instruction": user_instruction,
                },
                user_content=user_instruction,
            )

            samples = list(llm_output.samples_distributed)
            for sample_name, quantity in llm_output.sample_quantities.items():
                formatted = f"{sample_name} x{quantity}"
                if formatted not in samples and sample_name not in samples:
                    samples.append(formatted)

            interaction_patch = {}
            if llm_output.materials_shared:
                interaction_patch["materials_shared"] = self._merge_list_values(
                    current_draft.materials_shared,
                    llm_output.materials_shared,
                )
            if samples:
                interaction_patch["samples_distributed"] = self._merge_list_values(
                    current_draft.samples_distributed,
                    samples,
                )
            if llm_output.notes:
                interaction_patch["additional_notes"] = self._append_note(
                    current_draft.additional_notes,
                    llm_output.notes,
                )

            if not interaction_patch:
                return self.failure(
                    self.name,
                    "No materials or samples were identified in the request.",
                )

            return self.success(
                self.name,
                "Materials and samples updated in the interaction draft.",
                interaction_patch=interaction_patch,
                metadata={
                    "materials_update": llm_output.model_dump(mode="json"),
                },
            )
        except RuntimeError as exc:
            logger.error("MaterialsAndSamplesTool LLM failure: %s", str(exc), exc_info=exc)
            return self.failure(
                self.name,
                "I could not extract materials or samples right now. "
                "Please try again with a short message like \"Shared CardioMax brochure\".",
            )
        except Exception as exc:
            logger.error("MaterialsAndSamplesTool failed: %s", str(exc), exc_info=exc)
            return self.failure(
                self.name,
                "I could not update materials or samples right now. Please try again in a moment.",
            )

    @staticmethod
    def _merge_list_values(existing: list[str], incoming: list[str]) -> list[str]:
        """Merge list values without duplicates."""
        merged = list(existing)
        for item in incoming:
            if item not in merged:
                merged.append(item)
        return merged

    @staticmethod
    def _append_note(existing: str | None, note: str) -> str:
        """Append a note to existing additional notes."""
        if existing:
            return f"{existing}\n{note}".strip()
        return note


materials_and_samples_tool = MaterialsAndSamplesTool()
