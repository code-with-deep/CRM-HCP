"""Base class and helpers for Healthcare CRM LangGraph tools."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ValidationError

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.langgraph.memory import extract_latest_user_message, serialize_messages_for_prompt
from app.langgraph.schemas import ToolName
from app.langgraph.state import AgentState, InteractionDraft, get_interaction_draft
from app.langgraph.tools.dependencies import ToolDependencies
from app.langgraph.tools.schemas import ToolExecutionResult
from app.prompts.prompt_loader import render_tool_prompt

logger = get_logger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class BaseCrmTool(ABC):
    """Abstract base for enterprise LangGraph CRM tools."""

    name: ToolName
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    prompt_name: str

    @abstractmethod
    async def execute(
        self,
        *,
        state: AgentState,
        tool_input: dict[str, Any],
        dependencies: ToolDependencies,
    ) -> ToolExecutionResult:
        """Execute the tool using the current graph state."""

    def to_langchain_tool(self) -> StructuredTool:
        """Expose the CRM tool as a LangChain StructuredTool."""

        async def _invoke(**kwargs: Any) -> dict[str, Any]:
            raise NotImplementedError(
                "Direct LangChain invocation requires graph state. "
                "Use execute() through the LangGraph tool executor node.",
            )

        return StructuredTool.from_function(
            coroutine=_invoke,
            name=self.name.value,
            description=self.description,
            args_schema=self.input_schema,
        )

    async def invoke_structured_llm(
        self,
        *,
        dependencies: ToolDependencies,
        output_schema: type[SchemaT],
        prompt_name: str,
        prompt_kwargs: dict[str, Any],
        user_content: str,
    ) -> SchemaT:
        """Invoke the LLM with structured output and bounded retries."""
        settings = get_settings()
        prompt = render_tool_prompt(prompt_name, **prompt_kwargs)
        max_retries = settings.LLM_MAX_VALIDATION_RETRIES
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                result = await dependencies.llm_service.ainvoke_structured(
                    schema=output_schema,
                    node_prompt=prompt,
                    user_content=user_content,
                )
                return output_schema.model_validate(result.model_dump())
            except (ValidationError, ValueError, TypeError) as exc:
                last_error = exc
                logger.warning(
                    "Structured output validation failed for %s (attempt %s/%s): %s",
                    self.name.value,
                    attempt + 1,
                    max_retries + 1,
                    str(exc),
                )

        raise RuntimeError(
            f"Failed to obtain valid structured output for {self.name.value}: {last_error}",
        )

    def build_user_instruction(
        self,
        state: AgentState,
        tool_input: dict[str, Any],
    ) -> str:
        """Resolve the user instruction from router input or latest message."""
        instruction = tool_input.get("user_instruction")
        if isinstance(instruction, str) and instruction.strip():
            return instruction.strip()

        latest_message = extract_latest_user_message(state.get("messages", []))
        return latest_message or ""

    def serialize_history(self, state: AgentState) -> str:
        """Serialize recent conversation history for tool prompts."""
        return serialize_messages_for_prompt(state.get("messages", []))

    def current_draft_json(self, state: AgentState) -> str:
        """Serialize the current interaction draft."""
        return json.dumps(get_interaction_draft(state).to_serializable(), ensure_ascii=True)

    @staticmethod
    def map_interaction_schema_to_patch(
        output: BaseModel,
        *,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Map prompt-layer interaction schema fields to draft patch fields."""
        payload = output.model_dump()
        patch: dict[str, Any] = {}

        scalar_fields = {
            "hcp_name",
            "interaction_type",
            "interaction_date",
            "interaction_time",
            "sentiment",
            "outcomes",
            "follow_up_actions",
            "additional_notes",
        }
        list_fields = {
            "attendees",
            "topics_discussed",
            "materials_shared",
            "samples_distributed",
        }

        candidate_fields = fields or list(scalar_fields | list_fields)
        for field_name in candidate_fields:
            if field_name not in payload:
                continue
            value = payload[field_name]
            if value is None or value == [] or value == "":
                continue
            patch[field_name] = value

        products = payload.get("products") or []
        if products:
            existing_topics = patch.get("topics_discussed", [])
            merged_topics = list(existing_topics)
            for product in products:
                if product not in merged_topics:
                    merged_topics.append(product)
            patch["topics_discussed"] = merged_topics

        professional_summary = payload.get("professional_summary")
        if professional_summary:
            existing_notes = patch.get("additional_notes")
            patch["additional_notes"] = (
                f"{existing_notes}\n{professional_summary}".strip()
                if existing_notes
                else professional_summary
            )

        return patch

    @staticmethod
    def diff_interaction_drafts(
        current: InteractionDraft,
        updated: dict[str, Any],
        *,
        fields_updated: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a surgical patch by comparing current and updated drafts."""
        current_data = current.model_dump()
        patch: dict[str, Any] = {}

        if fields_updated:
            candidate_fields = fields_updated
        else:
            candidate_fields = list(updated.keys())

        for field_name in candidate_fields:
            if field_name not in current_data and field_name not in updated:
                continue

            new_value = updated.get(field_name)
            old_value = current_data.get(field_name)

            if new_value != old_value:
                patch[field_name] = new_value

        return patch

    @staticmethod
    def failure(
        tool_name: ToolName,
        message: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ToolExecutionResult:
        """Create a standardized failure payload."""
        return ToolExecutionResult(
            success=False,
            tool_name=tool_name.value,
            message=message,
            metadata=metadata or {},
        )

    @staticmethod
    def success(
        tool_name: ToolName,
        message: str,
        *,
        interaction_patch: dict[str, Any] | None = None,
        hcp_context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolExecutionResult:
        """Create a standardized success payload."""
        return ToolExecutionResult(
            success=True,
            tool_name=tool_name.value,
            message=message,
            interaction_patch=interaction_patch or {},
            hcp_context=hcp_context,
            metadata=metadata or {},
        )
