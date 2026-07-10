"""Domain enumerations for the Healthcare CRM database."""

import enum


class UserRole(str, enum.Enum):
    """Application roles for CRM users."""

    ADMIN = "admin"
    MEDICAL_REPRESENTATIVE = "medical_representative"
    MANAGER = "manager"


class Sentiment(str, enum.Enum):
    """Observed or inferred HCP sentiment during an interaction."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class InteractionStatus(str, enum.Enum):
    """Lifecycle status of an HCP interaction record."""

    DRAFT = "draft"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    """Role of a participant in an AI conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class HcpStatus(str, enum.Enum):
    """Operational status of a healthcare professional record."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"


class MaterialType(str, enum.Enum):
    """Classification of promotional or educational materials."""

    BROCHURE = "brochure"
    CLINICAL_STUDY = "clinical_study"
    PRODUCT_LEAFLET = "product_leaflet"
    PRESENTATION = "presentation"
    OTHER = "other"


class ToolExecutionStatus(str, enum.Enum):
    """Execution outcome for LangGraph tool invocations."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class ConversationSessionStatus(str, enum.Enum):
    """Lifecycle status of an AI conversation session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
