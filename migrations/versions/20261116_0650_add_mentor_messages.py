"""ИИ-наставник: история сообщений чата

Идентификатор: 5adc3750385b
Предыдущая миграция: 2dae8f06eaa2
Создана: 2026-11-16 06:50:55.310619
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Служебные поля Alembic: по ним он выстраивает миграции в цепочку.
revision: str = "5adc3750385b"
down_revision: str | None = "2dae8f06eaa2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применить изменения: создать таблицу сообщений наставника."""
    op.create_table(
        "mentor_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("mentor_messages", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_mentor_messages_topic_id"), ["topic_id"], unique=False)


def downgrade() -> None:
    """Откатить изменения: удалить таблицу."""
    with op.batch_alter_table("mentor_messages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mentor_messages_topic_id"))

    op.drop_table("mentor_messages")
