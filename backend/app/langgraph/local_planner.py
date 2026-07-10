"""High-confidence local planner for CRM turns when LLM is unavailable or unnecessary.

Keeps LangGraph as the orchestration layer. Complex free-form logging still prefers
the LLM; this module covers well-formed CRM intents and draft-aware clarifications
so demos remain reliable under Groq rate limits.
"""

from __future__ import annotations

from datetime import date, timedelta
import re

from app.langgraph.draft_messages import draft_log_example, draft_rate_limit_message, draft_retry_message
from app.langgraph.schemas import AgentIntent, PlannerOutput, ToolExtractionHints, ToolName
from app.langgraph.state import AgentState, InteractionDraft, get_interaction_draft
from app.langgraph.topic_extraction import extract_topics_from_message

_SENTIMENT_RE = re.compile(r"\b(positive|neutral|negative)\b", re.IGNORECASE)
_HELP_RE = re.compile(
    r"\b(help|how can you help|what can you do|capabilities|assist me)\b",
    re.IGNORECASE,
)
_HCP_RE = re.compile(
    r"\b(?:Dr\.?|DR\.?|doctor)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
)
_HCP_STOPWORDS = {
    "today",
    "tomorrow",
    "yesterday",
    "about",
    "to",
    "and",
    "with",
    "at",
    "on",
    "for",
    "the",
    "a",
    "an",
}
_HCP_CHANGE_RE = re.compile(
    r"(?:change|update|rename|actually|was|correct).*?(?:doctor|hcp|name).*?"
    r"(?:to|as|is)\s+(?:dr\.?\s*)?([A-Za-z][A-Za-z\s\.]+)",
    re.IGNORECASE,
)
_FOLLOW_UP_RE = re.compile(
    r"\b(follow[-\s]?up|followup|next step|reminder)\b",
    re.IGNORECASE,
)
_OUTCOME_RE = re.compile(r"\b(outcome|agreement|agreed|interested)\b", re.IGNORECASE)
_SEARCH_RE = re.compile(r"\b(find|search|look up|lookup)\b", re.IGNORECASE)
_MATERIALS_RE = re.compile(
    r"\b(material|brochure|leaflet|presentation|shared)\b",
    re.IGNORECASE,
)
_SAMPLES_RE = re.compile(r"\b(sample|samples)\b", re.IGNORECASE)
_LOG_RE = re.compile(
    r"\b(met|meet|meeting|called|call|visited|visit|discussed|discuss)\b",
    re.IGNORECASE,
)
_DATE_CHANGE_RE = re.compile(
    r"\b(change|update|set|make)\b.*\b(date|time)\b|\b(date|time)\b.*\b(to|as)\b",
    re.IGNORECASE,
)
_WEEKDAY_RE = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)
_RELATIVE_DATE_RE = re.compile(r"\b(today|yesterday|tomorrow)\b", re.IGNORECASE)
_MEET_AGAIN_RE = re.compile(
    r"\b(meet\s+ag(?:ai|ia)n|meet\s+again|see\s+again|come\s+back)\b",
    re.IGNORECASE,
)
_CONTINUATION_RE = re.compile(
    r"\b(he|she|they)\s+(told|asked|said|wants?|wanted)\b",
    re.IGNORECASE,
)
_NEXT_WEEKDAY_RE = re.compile(
    r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)
_SENTIMENT_CONTEXT_RE = re.compile(
    r"\b(was|were|is|are)\s+(positive|neutral|negative)\b",
    re.IGNORECASE,
)

_HELP_MESSAGE = (
    "I can help you log and update HCP interactions through chat. "
    "Try messages like:\n"
    "• \"I met Dr Sharma today to discuss CardioMax efficacy. Sentiment was positive.\"\n"
    "• \"Change the doctor name to Dr John.\"\n"
    "• \"Find Dr Gupta at Apollo Hospital.\"\n"
    "• \"Shared CardioMax brochure and 2 sample packs.\"\n"
    "• \"Outcome: interested in trial; follow up next Friday.\"\n\n"
    "The left form is AI-controlled — describe changes here and I will update it for you."
)


def _clarification(message: str, *, intent: AgentIntent = AgentIntent.GENERAL_ASSISTANCE) -> PlannerOutput:
    return PlannerOutput(
        objective="Ask a clarifying question before updating the CRM draft.",
        requires_tool_execution=False,
        context_summary="Draft-aware clarification required.",
        primary_intent=intent,
        confidence=0.9,
        reasoning="Missing interaction context or required details.",
        requires_clarification=True,
        clarification_question=message,
        selected_tool=ToolName.NONE,
        should_execute_tool=False,
        routing_reasoning="Clarification before tool execution.",
    )


def _has_base_interaction(draft: InteractionDraft) -> bool:
    return bool(draft.hcp_name or draft.interaction_date or draft.topics_discussed)


def _normalize_hcp_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _mentions_different_doctor(text: str, draft: InteractionDraft) -> bool:
    mentioned = _extract_hcp_name(text)
    if not mentioned or not draft.hcp_name:
        return False
    return _normalize_hcp_name(mentioned) != _normalize_hcp_name(draft.hcp_name)


def _is_draft_continuation(text: str, draft: InteractionDraft) -> bool:
    """Detect follow-up style messages that should update the active draft."""
    if not _has_base_interaction(draft):
        return False
    if _mentions_different_doctor(text, draft):
        return False

    lowered = text.lower()
    mentioned = _extract_hcp_name(text)
    if mentioned and draft.hcp_name:
        if _normalize_hcp_name(mentioned) == _normalize_hcp_name(draft.hcp_name):
            return any(
                token in lowered
                for token in ("again", "follow", "next monday", "next tuesday", "next wednesday", "next thursday", "next friday")
            )
        return False

    return bool(
        _CONTINUATION_RE.search(text)
        or _MEET_AGAIN_RE.search(text)
        or _NEXT_WEEKDAY_RE.search(text)
        or _FOLLOW_UP_RE.search(text)
        or any(
            phrase in lowered
            for phrase in (
                "next monday",
                "next tuesday",
                "next wednesday",
                "next thursday",
                "next friday",
                "next saturday",
                "next sunday",
            )
        )
        or (
            _WEEKDAY_RE.search(text)
            and any(token in lowered for token in ("next", "again", "agin", "told"))
        )
    )


def _build_follow_up_update(text: str, draft: InteractionDraft) -> PlannerOutput:
    """Plan a follow-up update against the current interaction draft."""
    lowered = text.lower()
    hcp = draft.hcp_name or "the current HCP"
    weekday = _NEXT_WEEKDAY_RE.search(text) or _WEEKDAY_RE.search(text)
    follow_up = text.strip()

    if weekday:
        day_name = weekday.group(1).capitalize()
        follow_date = _next_weekday(weekday.group(1)).isoformat()
        follow_up = f"Meet {hcp} again on {day_name} ({follow_date})."
    elif "tomorrow" in lowered:
        follow_up = (
            f"Follow up with {hcp} tomorrow "
            f"({(date.today() + timedelta(days=1)).isoformat()})."
        )
    else:
        follow_up = f"Follow up with {hcp}: {text.strip()}"

    return PlannerOutput(
        objective=f"Update follow-up for {hcp}.",
        requires_tool_execution=True,
        context_summary=f"Continuation update for active draft ({hcp}).",
        primary_intent=AgentIntent.UPDATE_FOLLOW_UP,
        confidence=0.96,
        reasoning="User continued the active interaction with a follow-up detail.",
        selected_tool=ToolName.OUTCOME_AND_FOLLOWUP,
        tool_input=ToolExtractionHints(
            user_instruction=text,
            follow_up_actions=follow_up,
        ),
        should_execute_tool=True,
    )


def _extract_log_sentiment(text: str, lowered: str) -> str | None:
    sentiment_match = _SENTIMENT_RE.search(text)
    if not sentiment_match:
        return None
    if "sentiment" in lowered or _SENTIMENT_CONTEXT_RE.search(text):
        return sentiment_match.group(1).lower()
    return None


def _next_weekday(name: str, *, reference: date | None = None) -> date:
    today = reference or date.today()
    target = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[name.lower()]
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def _resolve_relative_date(text: str) -> str | None:
    match = _RELATIVE_DATE_RE.search(text)
    if not match:
        return None
    token = match.group(1).lower()
    today = date.today()
    if token == "today":
        return today.isoformat()
    if token == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    if token == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    return None


def _extract_hcp_name(text: str) -> str | None:
    change = _HCP_CHANGE_RE.search(text)
    if change:
        name = change.group(1).strip(" .,")
        parts = [
            part
            for part in name.split()
            if part.lower() not in _HCP_STOPWORDS and part.lower() not in {"dr", "dr."}
        ]
        if not parts:
            return None
        cleaned = " ".join(parts)
        if not cleaned.lower().startswith("dr"):
            cleaned = f"Dr {cleaned}"
        else:
            cleaned = re.sub(r"^dr\.?\s*", "Dr ", cleaned, flags=re.IGNORECASE).strip()
        return cleaned
    match = _HCP_RE.search(text)
    if match:
        return f"Dr {match.group(1).strip()}"
    # Fallback for lowercase "dr sharma"
    loose = re.search(
        r"\b(?:dr\.?|doctor)\s+([A-Za-z]+)(?:\s+([A-Za-z]+))?",
        text,
        re.IGNORECASE,
    )
    if loose:
        first = loose.group(1)
        second = loose.group(2)
        if first.lower() in _HCP_STOPWORDS:
            return None
        if second and second.lower() in _HCP_STOPWORDS:
            second = None
        full = first.title() if second is None else f"{first.title()} {second.title()}"
        return f"Dr {full}"
    return None


def _extract_products(text: str, topics: list[str]) -> list[str]:
    products: list[str] = []
    for match in re.finditer(r"\b([A-Z][a-zA-Z0-9]*(?:Max|Pro|X))\b", text):
        product = match.group(1)
        if product not in products:
            products.append(product)
    if not products:
        for topic in topics:
            for match in re.finditer(r"\b([A-Z][a-zA-Z0-9]*(?:Max|Pro|X))\b", topic):
                product = match.group(1)
                if product not in products:
                    products.append(product)
    return products


def plan_from_local_rules(state: AgentState, text: str) -> PlannerOutput | None:
    """Return a planner decision for high-confidence CRM utterances, else None."""
    if not text or not text.strip():
        return None

    draft = get_interaction_draft(state)
    lowered = text.lower().strip()

    if _HELP_RE.search(text) or lowered in {"hi", "hello", "hey"}:
        return PlannerOutput(
            objective="Explain assistant capabilities.",
            requires_tool_execution=False,
            context_summary="Help request.",
            primary_intent=AgentIntent.GENERAL_ASSISTANCE,
            confidence=0.98,
            reasoning="User asked for help.",
            requires_clarification=True,
            clarification_question=_HELP_MESSAGE,
            selected_tool=ToolName.NONE,
            should_execute_tool=False,
        )

    if _is_draft_continuation(text, draft):
        return _build_follow_up_update(text, draft)

    # Sentiment-only updates (do not steal full log utterances that also mention sentiment).
    sentiment_match = _SENTIMENT_RE.search(text)
    is_log_utterance = bool(_LOG_RE.search(text) and _extract_hcp_name(text))
    if (
        sentiment_match
        and not is_log_utterance
        and any(token in lowered for token in ("sentiment", "update", "set", "change", "make"))
    ):
        if not _has_base_interaction(draft):
            return _clarification(
                "I can set the sentiment once we have an interaction on the form. "
                f"Please describe the meeting first — {draft_log_example(draft)}",
                intent=AgentIntent.EDIT_INTERACTION,
            )
        sentiment = sentiment_match.group(1).lower()
        return PlannerOutput(
            objective=f"Update sentiment to {sentiment}.",
            requires_tool_execution=True,
            context_summary="Sentiment edit.",
            primary_intent=AgentIntent.EDIT_INTERACTION,
            confidence=0.95,
            reasoning="Explicit sentiment update.",
            selected_tool=ToolName.EDIT_INTERACTION,
            tool_input=ToolExtractionHints(user_instruction=text, sentiment=sentiment),
            should_execute_tool=True,
        )

    # Follow-up / outcome updates.
    if _FOLLOW_UP_RE.search(text) or (
        "change follow" in lowered or lowered.startswith("follow")
    ):
        if not _has_base_interaction(draft):
            return _clarification(
                "There isn't an interaction draft yet, so I don't have a meeting to attach "
                f"a follow-up to. {draft_log_example(draft)}",
                intent=AgentIntent.UPDATE_FOLLOW_UP,
            )
        weekday = _WEEKDAY_RE.search(text)
        follow_up = text.strip()
        if weekday:
            day_name = weekday.group(1).capitalize()
            follow_date = _next_weekday(weekday.group(1)).isoformat()
            follow_up = f"Follow up on {day_name} ({follow_date})."
        elif "tomorrow" in lowered:
            follow_up = f"Follow up tomorrow ({(date.today() + timedelta(days=1)).isoformat()})."
        return PlannerOutput(
            objective="Update follow-up actions.",
            requires_tool_execution=True,
            context_summary="Follow-up edit on existing draft.",
            primary_intent=AgentIntent.UPDATE_FOLLOW_UP,
            confidence=0.93,
            reasoning="Explicit follow-up update with existing interaction context.",
            selected_tool=ToolName.OUTCOME_AND_FOLLOWUP,
            tool_input=ToolExtractionHints(
                user_instruction=text,
                follow_up_actions=follow_up,
            ),
            should_execute_tool=True,
        )

    if _OUTCOME_RE.search(text) and any(
        token in lowered for token in ("outcome", "update", "set", "change", "add")
    ):
        if not _has_base_interaction(draft):
            return _clarification(
                "I can capture outcomes after we log the interaction. "
                "Please describe the meeting first, then share the outcome.",
                intent=AgentIntent.UPDATE_OUTCOMES,
            )
        outcome_text = re.sub(
            r"^(?:outcome|outcomes)\s*[:\-]?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        return PlannerOutput(
            objective="Update outcomes.",
            requires_tool_execution=True,
            context_summary="Outcome update.",
            primary_intent=AgentIntent.UPDATE_OUTCOMES,
            confidence=0.9,
            selected_tool=ToolName.OUTCOME_AND_FOLLOWUP,
            tool_input=ToolExtractionHints(
                user_instruction=text,
                outcomes=outcome_text or text,
            ),
            should_execute_tool=True,
        )

    # Date/time edits need an existing interaction.
    if _DATE_CHANGE_RE.search(text) and not _LOG_RE.search(text):
        if not _has_base_interaction(draft):
            return _clarification(
                "I don't have a meeting on the form yet, so I can't update the date or time. "
                f"{draft_log_example(draft)}",
                intent=AgentIntent.EDIT_INTERACTION,
            )
        patch = ToolExtractionHints(user_instruction=text)
        resolved = _resolve_relative_date(text)
        if resolved and "date" in lowered:
            patch.interaction_date = resolved
        time_match = re.search(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b", text)
        if time_match and "time" in lowered:
            patch.interaction_time = time_match.group(1)
        if patch.interaction_date or patch.interaction_time:
            return PlannerOutput(
                objective="Update interaction date/time.",
                requires_tool_execution=True,
                context_summary="Date/time edit on existing draft.",
                primary_intent=AgentIntent.EDIT_INTERACTION,
                confidence=0.9,
                selected_tool=ToolName.EDIT_INTERACTION,
                tool_input=patch,
                should_execute_tool=True,
            )

    # HCP rename / edit.
    if any(token in lowered for token in ("change", "update", "rename", "actually", "correct")) and (
        "doctor" in lowered or "hcp" in lowered or "name" in lowered
    ):
        if not _has_base_interaction(draft):
            return _clarification(
                "There is no interaction draft yet. Please log the meeting first, "
                "then I can correct the HCP name.",
                intent=AgentIntent.EDIT_INTERACTION,
            )
        hcp_name = _extract_hcp_name(text)
        if hcp_name:
            return PlannerOutput(
                objective=f"Update HCP name to {hcp_name}.",
                requires_tool_execution=True,
                context_summary="HCP name correction.",
                primary_intent=AgentIntent.EDIT_INTERACTION,
                confidence=0.92,
                selected_tool=ToolName.EDIT_INTERACTION,
                tool_input=ToolExtractionHints(user_instruction=text, hcp_name=hcp_name),
                should_execute_tool=True,
            )

    # Search HCP.
    if _SEARCH_RE.search(text):
        hcp_name = _extract_hcp_name(text)
        hospital_match = re.search(r"\bat\s+([A-Za-z][A-Za-z\s]+Hospital)", text, re.IGNORECASE)
        return PlannerOutput(
            objective="Search for an HCP.",
            requires_tool_execution=True,
            context_summary="HCP search request.",
            primary_intent=AgentIntent.SEARCH_HCP,
            confidence=0.9,
            selected_tool=ToolName.SEARCH_HCP,
            tool_input=ToolExtractionHints(
                user_instruction=text,
                doctor_name=hcp_name,
                hcp_name=hcp_name,
                hospital=hospital_match.group(1).strip() if hospital_match else None,
            ),
            should_execute_tool=True,
        )

    # Materials / samples.
    if _MATERIALS_RE.search(text) or _SAMPLES_RE.search(text):
        vague = any(
            phrase in lowered
            for phrase in (
                "ask me which",
                "which brochures",
                "which materials",
                "which samples",
                "please ask",
                "add materials shared",
                "add samples distributed",
            )
        ) or lowered in {"add materials", "add samples"}
        if vague:
            return _clarification(
                "Sure — which materials or samples should I add? "
                "For example: \"Shared CardioMax brochure and dosing leaflet\" "
                "or \"Distributed 2 CardioMax sample packs\".",
                intent=AgentIntent.UPDATE_MATERIALS,
            )
        if not _has_base_interaction(draft):
            return _clarification(
                "I can add materials once an interaction is on the form. "
                "Please log the meeting first, then tell me what was shared.",
                intent=AgentIntent.UPDATE_MATERIALS,
            )
        materials: list[str] = []
        samples: list[str] = []
        if "brochure" in lowered:
            materials.append("Brochures")
        if "leaflet" in lowered:
            materials.append("Leaflet")
        if "presentation" in lowered:
            materials.append("Presentation")
        if _SAMPLES_RE.search(text):
            qty = re.search(r"\b(\d+)\b", text)
            samples.append(f"Sample packs x{qty.group(1)}" if qty else "Sample packs")
        if materials or samples:
            return PlannerOutput(
                objective="Update materials and samples.",
                requires_tool_execution=True,
                context_summary="Materials/samples update on existing draft.",
                primary_intent=AgentIntent.UPDATE_MATERIALS,
                confidence=0.9,
                selected_tool=ToolName.MATERIALS_AND_SAMPLES,
                tool_input=ToolExtractionHints(
                    user_instruction=text,
                    materials_shared=materials,
                    samples_distributed=samples,
                ),
                should_execute_tool=True,
            )

    # New interaction log.
    if _LOG_RE.search(text) and _extract_hcp_name(text):
        hcp_name = _extract_hcp_name(text)
        interaction_type = "Meeting"
        if "call" in lowered:
            interaction_type = "Call"
        elif "visit" in lowered:
            interaction_type = "Visit"
        topics = extract_topics_from_message(text)
        products = _extract_products(text, topics)
        sentiment = _extract_log_sentiment(text, lowered)
        materials: list[str] = []
        if "brochure" in lowered:
            materials.append("Brochures")
        interaction_date = _resolve_relative_date(text) or date.today().isoformat()
        return PlannerOutput(
            objective=f"Log interaction with {hcp_name}.",
            requires_tool_execution=True,
            context_summary="Natural-language interaction log.",
            primary_intent=AgentIntent.LOG_INTERACTION,
            confidence=0.9,
            selected_tool=ToolName.LOG_INTERACTION,
            tool_input=ToolExtractionHints(
                user_instruction=text,
                hcp_name=hcp_name,
                interaction_type=interaction_type,
                interaction_date=interaction_date,
                topics_discussed=topics,
                products=products,
                sentiment=sentiment,
                materials_shared=materials,
            ),
            should_execute_tool=True,
        )

    return None
