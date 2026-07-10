"""Groq LLM factory and structured output helpers."""

from functools import lru_cache
import asyncio
import json
import re
from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel

from app.config.settings import Settings, get_settings
from app.core.logging import get_logger
from app.prompts.prompt_loader import load_prompt

logger = get_logger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)

_FUNCTION_JSON_RE = re.compile(
    r"<function=\w+>\s*(\{.*\})\s*(?:</function>)?$",
    re.DOTALL,
)
_RETRY_AFTER_RE = re.compile(r"try again in ([0-9.]+)s", re.IGNORECASE)


class LLMService:
    """Configurable Groq LLM service for LangGraph nodes."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._primary_model = self._build_model(self._settings.GROQ_MODEL_NAME)
        self._fallback_model = self._build_model(self._settings.GROQ_FALLBACK_MODEL_NAME)

    def _build_model(self, model_name: str) -> BaseChatModel:
        """Create a ChatGroq instance for the requested model."""
        return ChatGroq(
            api_key=self._settings.GROQ_API_KEY,
            model=model_name,
            temperature=self._settings.LLM_TEMPERATURE,
            timeout=self._settings.LLM_TIMEOUT_SECONDS,
            max_tokens=self._settings.LLM_MAX_TOKENS,
            # Avoid multi-second Groq SDK retries; we handle fallback ourselves.
            max_retries=0,
        )

    @property
    def primary_model(self) -> BaseChatModel:
        """Return the configured primary model."""
        return self._primary_model

    @property
    def fallback_model(self) -> BaseChatModel:
        """Return the configured fallback model."""
        return self._fallback_model

    def with_structured_output(self, schema: type[SchemaT]) -> BaseChatModel:
        """Bind structured output to the primary model."""
        return self._primary_model.with_structured_output(schema)

    async def ainvoke_structured(
        self,
        *,
        schema: type[SchemaT],
        node_prompt: str,
        user_content: str,
    ) -> SchemaT:
        """Invoke the LLM with system + node prompt and return structured output."""
        messages: list[BaseMessage] = [
            SystemMessage(content=load_prompt("system")),
            SystemMessage(content=node_prompt),
            HumanMessage(content=user_content),
        ]
        structured_llm = self.with_structured_output(schema)

        try:
            result = await structured_llm.ainvoke(messages)
            if isinstance(result, schema):
                return result
            return schema.model_validate(result)
        except Exception as primary_error:
            recovered = self._try_recover_structured(schema, primary_error)
            if recovered is not None:
                logger.warning(
                    "Recovered structured output from primary failure: %s",
                    type(primary_error).__name__,
                )
                return recovered

            if self._is_rate_limit_error(primary_error):
                wait_seconds = self._rate_limit_wait_seconds(primary_error)
                logger.warning(
                    "Primary model rate-limited; retrying once after %.1fs",
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)
                try:
                    result = await structured_llm.ainvoke(messages)
                    if isinstance(result, schema):
                        return result
                    return schema.model_validate(result)
                except Exception as retry_error:
                    recovered = self._try_recover_structured(schema, retry_error)
                    if recovered is not None:
                        return recovered
                    logger.warning(
                        "Primary retry still rate-limited; not using fallback: %s",
                        str(retry_error),
                    )
                    raise retry_error

            logger.warning(
                "Primary model structured invocation failed: %s. Trying fallback.",
                str(primary_error),
            )
            try:
                fallback_llm = self._fallback_model.with_structured_output(schema)
                result = await fallback_llm.ainvoke(messages)
                if isinstance(result, schema):
                    return result
                return schema.model_validate(result)
            except Exception as fallback_error:
                recovered = self._try_recover_structured(schema, fallback_error)
                if recovered is not None:
                    return recovered
                raise fallback_error from primary_error

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Detect Groq/OpenAI-style rate limit failures."""
        name = type(error).__name__.lower()
        message = str(error).lower()
        return (
            "ratelimit" in name
            or "rate_limit" in message
            or "rate limit" in message
            or "429" in message
        )

    @staticmethod
    def _rate_limit_wait_seconds(error: Exception) -> float:
        """Parse Groq retry hint, defaulting to a short pause."""
        match = _RETRY_AFTER_RE.search(str(error))
        if match:
            return min(max(float(match.group(1)) + 0.25, 1.0), 8.0)
        return 2.5

    @staticmethod
    def _try_recover_structured(schema: type[SchemaT], error: Exception) -> SchemaT | None:
        """Best-effort parse when Groq returns tool_use_failed with embedded JSON."""
        message = str(error)
        payload: Any = None

        match = _FUNCTION_JSON_RE.search(message)
        if match:
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                payload = None

        if payload is None:
            # Some SDK errors embed the generation after failed_generation.
            gen_match = re.search(
                r"failed_generation['\"]:\s*['\"](.+?)(?:['\"]\s*[,}])",
                message,
                re.DOTALL,
            )
            if gen_match:
                raw = gen_match.group(1)
                raw = raw.encode("utf-8").decode("unicode_escape")
                fn_match = _FUNCTION_JSON_RE.search(raw) or re.search(r"(\{.*\})", raw, re.DOTALL)
                if fn_match:
                    try:
                        payload = json.loads(fn_match.group(1))
                    except json.JSONDecodeError:
                        payload = None

        if not isinstance(payload, dict):
            return None
        try:
            return schema.model_validate(payload)
        except Exception:
            return None

    async def ainvoke_text(self, *, node_prompt: str, user_content: str) -> str:
        """Invoke the LLM and return plain text output."""
        messages: list[BaseMessage] = [
            SystemMessage(content=load_prompt("system")),
            SystemMessage(content=node_prompt),
            HumanMessage(content=user_content),
        ]

        try:
            response = await self._primary_model.ainvoke(messages)
        except Exception as primary_error:
            logger.warning(
                "Primary model text invocation failed: %s. Trying fallback.",
                str(primary_error),
            )
            response = await self._fallback_model.ainvoke(messages)

        content = response.content
        if isinstance(content, str):
            return content
        return str(content)


@lru_cache
def get_llm_service() -> LLMService:
    """Return a cached LLM service instance."""
    return LLMService()
