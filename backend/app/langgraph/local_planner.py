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

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_SENTIMENT_RE = re.compile(r"\b(positive|neutral|negative)\b", re.IGNORECASE)

# Implicit / soft sentiment phrases
_SOFT_POSITIVE_RE = re.compile(
    r"\b(?:went\s+(?:really\s+)?well|very\s+(?:interested|receptive|engaged|enthusiastic)|"
    r"great\s+(?:meeting|call|visit|response|reception)|(?:happy|pleased|excited)\s+(?:with|about)|"
    r"showed\s+(?:great\s+)?interest|keen\s+to|looking\s+forward|appreciated|impressed)\b",
    re.IGNORECASE,
)
_SOFT_NEGATIVE_RE = re.compile(
    r"\b(?:not\s+(?:very\s+)?receptive|wasn't\s+(?:very\s+)?(?:interested|receptive|engaged)|"
    r"didn't\s+go\s+(?:well|great)|(?:reluctant|hesitant|skeptical|sceptical|resistant|uninterested)|"
    r"wasn't\s+(?:happy|pleased)|not\s+(?:happy|pleased|interested|keen)|"
    r"difficult\s+(?:meeting|call|conversation)|(?:hard\s+to\s+convince|cold\s+reception))\b",
    re.IGNORECASE,
)

_HELP_RE = re.compile(
    r"\b(help|how can you help|what can you do|capabilities|assist me)\b",
    re.IGNORECASE,
)

# HCP name patterns — now supports initials like Dr A.K. Gupta
_HCP_RE = re.compile(
    r"\b(?:Dr\.?|DR\.?|doctor)\s+"
    r"([A-Z](?:\.[A-Z]\.?)*\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
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
    "up",
    "back",
    "again",
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
    r"\b(material|brochure|leaflet|presentation|shared|pamphlet|flyer|handout|literature)\b",
    re.IGNORECASE,
)
_SAMPLES_RE = re.compile(r"\b(sample|samples)\b", re.IGNORECASE)

# Extended: "had a meeting/call/visit", "attended", "spoke with"
_LOG_RE = re.compile(
    r"\b(met|meet|meeting|called|call|visited|visit|discussed|discuss"
    r"|had\s+a\s+(?:meeting|call|visit|chat|face\s+to\s+face|virtual|conference)"
    r"|attended|spoke\s+(?:to|with)|spoken\s+(?:to|with)|caught\s+up\s+with"
    r"|rang(?:\s+up)?|popped\s+(?:in|by)|dropped\s+(?:in|by))\b",
    re.IGNORECASE,
)

# Interaction type detection
_FACE_TO_FACE_RE = re.compile(
    r"\b(face[\s\-]to[\s\-]face|f2f|in[\s\-]person|in\s+person\s+meeting|personal\s+visit|"
    r"popped\s+(?:in|by)|dropped\s+(?:in|by))\b",
    re.IGNORECASE,
)
_VIRTUAL_RE = re.compile(
    r"\b(virtual|online|video\s+call|zoom|teams|webex|google\s+meet|skype|web\s+meeting|"
    r"remote\s+meeting|video\s+meeting)\b",
    re.IGNORECASE,
)
_CONFERENCE_RE = re.compile(
    r"\b(conference|congress|symposium|seminar|webinar|summit|convention)\b",
    re.IGNORECASE,
)
_CALL_RE = re.compile(
    r"\b(call(?:ed)?|phone|rang(?:\s+up)?|telephone|tele(?:-)?call|over\s+the\s+phone)\b",
    re.IGNORECASE,
)

_DATE_CHANGE_RE = re.compile(
    r"\b(change|update|set|make|reschedule|move)\b.*\b(date|time|meeting|appointment)\b"
    r"|\b(date|time)\b.*\b(to|as)\b",
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

# Location / hospital extraction
_LOCATION_RE = re.compile(
    r"\bat\s+([A-Za-z][A-Za-z\s]+?(?:Hospital|Clinic|Centre|Center|Institute|Medical|Polyclinic|Healthcare))\b"
    r"|\b([A-Za-z][A-Za-z\s]+?(?:Hospital|Clinic|Centre|Center|Institute))\b",
    re.IGNORECASE,
)

# Product name patterns: CamelCase brand names AND known generic drug terms
_PRODUCT_BRAND_RE = re.compile(
    r"\b([A-Z][a-zA-Z0-9]{2,}(?:Max|Pro|X|Plus|Forte|SR|XR|ER|OD|CR|LA|MR)?)\b"
)
_GENERIC_DRUG_RE = re.compile(
    r"\b(metformin|lipitor|atorvastatin|amlodipine|ramipril|losartan|omeprazole|"
    r"pantoprazole|aspirin|clopidogrel|warfarin|insulin|glipizide|sitagliptin|"
    r"rosuvastatin|simvastatin|lisinopril|valsartan|telmisartan|bisoprolol|"
    r"carvedilol|furosemide|spironolactone|allopurinol|colchicine|febuxostat|"
    r"montelukast|salbutamol|tiotropium|budesonide|fluticasone|prednisolone|"
    r"dexamethasone|amoxicillin|azithromycin|ciprofloxacin|metronidazole|"
    r"fluconazole|acyclovir|oseltamivir|hydroxychloroquine|methotrexate)\b",
    re.IGNORECASE,
)

_HELP_MESSAGE = (
    "I can help you log and update HCP interactions through chat. "
    "Try messages like:\n"
    "• \"I met Dr Sharma today to discuss CardioMax efficacy.\"\n"
    "• \"Had a face-to-face with Dr Gupta — he was very interested.\"\n"
    "• \"Attended a conference with Dr Singh about hypertension.\"\n"
    "• \"Rang up Dr Patel about the quarterly review.\"\n"
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


def _extract_soft_sentiment(text: str) -> str | None:
    """Detect implicit/soft sentiment cues from natural language."""
    if _SOFT_POSITIVE_RE.search(text):
        return "positive"
    if _SOFT_NEGATIVE_RE.search(text):
        return "negative"
    return None


def _extract_log_sentiment(text: str, lowered: str) -> str | None:
    """Extract explicit or implicit sentiment from an interaction message."""
    # Explicit sentiment keyword
    sentiment_match = _SENTIMENT_RE.search(text)
    if sentiment_match:
        if "sentiment" in lowered or _SENTIMENT_CONTEXT_RE.search(text):
            return sentiment_match.group(1).lower()
    # Implicit/soft sentiment
    return _extract_soft_sentiment(text)


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
    """Extract HCP name, including initials like Dr A.K. Gupta."""
    # Change / rename pattern first
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

    # Primary pattern — supports initials (Dr A.K. Gupta → "Dr A.K. Gupta")
    match = _HCP_RE.search(text)
    if match:
        initials = (match.group(1) or "").strip()
        surname = match.group(2).strip()
        if surname.lower() in _HCP_STOPWORDS:
            return None
        full = f"{initials} {surname}".strip() if initials else surname
        return f"Dr {full}"

    # Fallback for lowercase "dr sharma"
    loose = re.search(
        r"\b(?:dr\.?|doctor)\s+([A-Za-z]+(?:\.[A-Za-z]\.?)?)(?:\s+([A-Za-z]+))?",
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


def _infer_interaction_type(text: str, lowered: str) -> str:
    """Infer the most specific interaction type from natural language."""
    if _FACE_TO_FACE_RE.search(text):
        return "Face to Face"
    if _CONFERENCE_RE.search(text):
        return "Conference"
    if _VIRTUAL_RE.search(text):
        return "Virtual Meeting"
    if _CALL_RE.search(text):
        return "Call"
    if "visit" in lowered:
        return "Visit"
    return "Meeting"


def _extract_products(text: str, topics: list[str]) -> list[str]:
    """Extract brand-name and generic drug products from text."""
    products: list[str] = []
    seen: set[str] = set()

    # Brand-name products (CamelCase with optional suffix)
    for match in _PRODUCT_BRAND_RE.finditer(text):
        product = match.group(1)
        key = product.lower()
        if key not in seen:
            seen.add(key)
            products.append(product)

    # Generic drug names
    for match in _GENERIC_DRUG_RE.finditer(text):
        product = match.group(1).title()
        key = product.lower()
        if key not in seen:
            seen.add(key)
            products.append(product)

    # Fall back to scanning topics
    if not products:
        for topic in topics:
            for match in _PRODUCT_BRAND_RE.finditer(topic):
                product = match.group(1)
                key = product.lower()
                if key not in seen:
                    seen.add(key)
                    products.append(product)

    return products


def _extract_location(text: str) -> str | None:
    """Extract hospital or clinic name from text."""
    match = _LOCATION_RE.search(text)
    if match:
        return (match.group(1) or match.group(2) or "").strip()
    return None


def _extract_time(text: str) -> str | None:
    """Extract time string from text (e.g. '10:30 AM', '14:00')."""
    match = re.search(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?|\d{1,2}\s*(?:AM|PM|am|pm))\b", text)
    return match.group(1).strip() if match else None


def _extract_sample_with_product(text: str) -> list[str]:
    """Extract sample entries including named product and quantity if present."""
    samples: list[str] = []
    # Pattern: "3 CardioMax samples", "2 packs of Lipitor"
    qty_product = re.finditer(
        r"\b(\d+)\s+(?:packs?\s+of\s+)?([A-Z][a-zA-Z0-9]+)\s+samples?\b"
        r"|\b([A-Z][a-zA-Z0-9]+)\s+samples?\s*(?:x|×)?\s*(\d+)\b",
        text,
        re.IGNORECASE,
    )
    for match in qty_product:
        if match.group(1) and match.group(2):
            samples.append(f"{match.group(2)} x{match.group(1)}")
        elif match.group(3) and match.group(4):
            samples.append(f"{match.group(3)} x{match.group(4)}")
    if not samples and _SAMPLES_RE.search(text):
        qty = re.search(r"\b(\d+)\b", text)
        samples.append(f"Sample packs x{qty.group(1)}" if qty else "Sample packs")
    return samples


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
        # weekday date resolution (e.g. "reschedule to Monday")
        weekday_match = _WEEKDAY_RE.search(text)
        if weekday_match and not patch.interaction_date:
            patch.interaction_date = _next_weekday(weekday_match.group(1)).isoformat()
        time_match = _extract_time(text)
        if time_match and "time" in lowered:
            patch.interaction_time = time_match
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
        hospital = _extract_location(text)
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
                hospital=hospital,
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
        if "brochure" in lowered:
            materials.append("Brochures")
        if "leaflet" in lowered:
            materials.append("Leaflet")
        if "presentation" in lowered:
            materials.append("Presentation")
        if "pamphlet" in lowered:
            materials.append("Pamphlet")
        if "flyer" in lowered:
            materials.append("Flyer")
        if "handout" in lowered:
            materials.append("Handout")
        if "literature" in lowered:
            materials.append("Literature")
        samples = _extract_sample_with_product(text) if _SAMPLES_RE.search(text) else []
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
        interaction_type = _infer_interaction_type(text, lowered)
        topics = extract_topics_from_message(text)
        products = _extract_products(text, topics)
        sentiment = _extract_log_sentiment(text, lowered)
        materials: list[str] = []
        if "brochure" in lowered:
            materials.append("Brochures")
        interaction_date = _resolve_relative_date(text) or date.today().isoformat()
        interaction_time = _extract_time(text)
        hospital = _extract_location(text)
        additional_notes = hospital if hospital else None
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
                interaction_time=interaction_time,
                topics_discussed=topics,
                products=products,
                sentiment=sentiment,
                materials_shared=materials,
                additional_notes=additional_notes,
            ),
            should_execute_tool=True,
        )

    return None
