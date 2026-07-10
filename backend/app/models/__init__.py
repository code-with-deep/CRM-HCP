"""ORM model registry for SQLAlchemy metadata and Alembic discovery."""

from app.models.conversation import ConversationMessage, ConversationSession
from app.models.hcp import Hcp
from app.models.interaction import Interaction
from app.models.interaction_associations import (
    InteractionAttendee,
    InteractionMaterial,
    InteractionProduct,
    InteractionSample,
    InteractionTopic,
)
from app.models.interaction_type import InteractionType
from app.models.material import Material
from app.models.product import Product
from app.models.sample import Sample
from app.models.tool_log import ToolExecutionLog
from app.models.topic import Topic
from app.models.user import User

__all__ = [
    "User",
    "Hcp",
    "InteractionType",
    "Product",
    "Material",
    "Sample",
    "Topic",
    "Interaction",
    "InteractionAttendee",
    "InteractionTopic",
    "InteractionMaterial",
    "InteractionSample",
    "InteractionProduct",
    "ConversationSession",
    "ConversationMessage",
    "ToolExecutionLog",
]
