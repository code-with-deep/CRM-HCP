"""LogInteractionTool implementation."""

from typing import Any

from app.core.logging import get_logger
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState
from app.langgraph.tools.base_tool import BaseCrmTool
from app.langgraph.tools.date_utils import normalize_interaction_patch
from app.langgraph.tools.dependencies import ToolDependencies
from app.langgraph.tools.schemas import LogInteractionToolInput, ToolExecutionResult
from app.prompts.schemas import LogInteractionOutput

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
    "products",
)


class LogInteractionTool(BaseCrmTool):
    """Create a new interaction draft from natural language."""

    name = ToolName.LOG_INTERACTION
    description = (
        "Extract and populate a new HCP interaction draft from the user's natural language "
        "description including HCP, type, date, attendees, topics, materials, samples, "
        "sentiment, outcomes, and follow-up details."
    )
    input_schema = LogInteractionToolInput
    output_schema = LogInteractionOutput
    prompt_name = "log_interaction"

    async def execute(
        self,
        *,
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        """Extract structured interaction data and return a draft patch."""
        try:
            validated_input = self.input_schema.model_validate(tool_input)
            router_hints = normalize_interaction_patch(
                self._extract_router_hints(validated_input),
            )
            user_instruction = validated_input.user_instruction or self.build_user_instruction(
                state,
                tool_input,
            )

            # Fast path: planner already extracted enough fields — skip a second LLM call.
            if self._hints_are_sufficient(router_hints):
                logger.info(
                    "LogInteractionTool using planner hints (skip LLM): %s",
                    list(router_hints.keys()),
                )
                return self.success(
                    self.name,
                    "Interaction draft populated from the conversation.",
                    interaction_patch=router_hints,
                    metadata={
                        "fields_populated": list(router_hints.keys()),
                        "source": "planner_hints",
                    },
                )

            llm_output = await self.invoke_structured_llm(
                dependencies=dependencies,
                output_schema=LogInteractionOutput,
                prompt_name=self.prompt_name,
                prompt_kwargs={
                    "conversation_history": self.serialize_history(state),
                    "current_interaction": "{}",
                },
                user_content=self._build_extraction_content(user_instruction, router_hints),
            )

            interaction_patch = self.map_interaction_schema_to_patch(
                llm_output,
                fields=llm_output.fields_populated or None,
            )

            # Merge router hints for any fields the extractor left empty.
            for field_name, value in router_hints.items():
                if field_name not in interaction_patch and value not in (None, "", []):
                    interaction_patch[field_name] = value

            interaction_patch = normalize_interaction_patch(interaction_patch)

            if not interaction_patch:
                return self.failure(
                    self.name,
                    "I could not extract interaction details from the message. "
                    "Please provide more specifics about the HCP interaction.",
                )

            logger.info(
                "LogInteractionTool populated fields: %s",
                list(interaction_patch.keys()),
            )

            return self.success(
                self.name,
                "Interaction draft populated from the conversation.",
                interaction_patch=interaction_patch,
                metadata={
                    "fields_populated": list(interaction_patch.keys()),
                    "professional_summary": llm_output.professional_summary,
                    "ai_generated_summary": llm_output.professional_summary,
                    "extracted_interaction": llm_output.model_dump(mode="json"),
                },
            )
        except RuntimeError as exc:
            logger.error("LogInteractionTool LLM failure: %s", str(exc), exc_info=exc)
            # Fall back to router hints if the LLM fails but hints exist.
            try:
                validated_input = self.input_schema.model_validate(tool_input)
                router_hints = normalize_interaction_patch(
                    self._extract_router_hints(validated_input),
                )
                if router_hints:
                    return self.success(
                        self.name,
                        "Interaction draft populated from extracted details.",
                        interaction_patch=router_hints,
                        metadata={"fields_populated": list(router_hints.keys()), "fallback": True},
                    )
            except Exception:
                pass
            return self.failure(self.name, "I could not process the interaction details right now.")
        except Exception as exc:
            logger.error("LogInteractionTool failed: %s", str(exc), exc_info=exc)
            return self.failure(self.name, f"Failed to log interaction: {exc}")

    @staticmethod
    def _hints_are_sufficient(hints: dict[str, Any]) -> bool:
        """Return True when planner hints can populate the draft without another LLM call."""
        if not hints.get("hcp_name"):
            return False
        # Date OR topics is enough to proceed; validator soft-warns on missing date.
        return bool(hints.get("interaction_date") or hints.get("topics_discussed"))

    @staticmethod
    def _extract_router_hints(validated_input: LogInteractionToolInput) -> dict[str, Any]:
        """Collect optional extraction hints provided by the tool router."""
        payload = validated_input.model_dump()
        hints: dict[str, Any] = {}
        for field_name in _HINT_FIELDS:
            value = payload.get(field_name)
            if value in (None, "", []):
                continue
            hints[field_name] = value

        products = hints.pop("products", None)
        if products:
            topics = list(hints.get("topics_discussed") or [])
            for product in products:
                already_covered = product in topics or any(
                    product.lower() in topic.lower() for topic in topics
                )
                if not already_covered:
                    topics.append(product)
            hints["topics_discussed"] = topics
        return hints

    @staticmethod
    def _build_extraction_content(user_instruction: str, router_hints: dict[str, Any]) -> str:
        """Build the user content for the extraction LLM call."""
        lines = [
            "Extract interaction fields ONLY from the latest user message below.",
            "Do not reuse products, topics, sentiment, or HCP details from earlier turns.",
            "If a field is not explicitly stated or clearly implied in the message, leave it null.",
            "",
            f"User message:\n{user_instruction}",
        ]
        if router_hints:
            lines.extend(
                [
                    "",
                    "Planner extraction hints (use only when consistent with the user message):",
                    str(router_hints),
                ],
            )
        return "\n".join(lines)


log_interaction_tool = LogInteractionTool()
