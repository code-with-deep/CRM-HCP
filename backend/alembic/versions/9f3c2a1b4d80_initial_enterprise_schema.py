"""Initial enterprise schema

Revision ID: 9f3c2a1b4d80
Revises:
Create Date: 2026-07-09 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

from app.database.base import Base
from app.models import (  # noqa: F401
    ConversationMessage,
    ConversationSession,
    Hcp,
    Interaction,
    InteractionAttendee,
    InteractionMaterial,
    InteractionProduct,
    InteractionSample,
    InteractionTopic,
    InteractionType,
    Material,
    Product,
    Sample,
    ToolExecutionLog,
    Topic,
    User,
)

# revision identifiers, used by Alembic.
revision: str = "9f3c2a1b4d80"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial enterprise Healthcare CRM schema."""
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    """Drop all tables created in the initial schema."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
