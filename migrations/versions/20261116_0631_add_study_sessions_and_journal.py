"""учёт времени и журнал: занятия и записи к темам

Идентификатор: 2dae8f06eaa2
Предыдущая миграция: c4a7b790cc9a
Создана: 2026-11-16 06:31:07.371740
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Служебные поля Alembic: по ним он выстраивает миграции в цепочку.
revision: str = "2dae8f06eaa2"
down_revision: str | None = "c4a7b790cc9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применить изменения: создать таблицы занятий и журнала."""
    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("journal_entries", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_journal_entries_topic_id"), ["topic_id"], unique=False)

    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("study_sessions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_study_sessions_day"), ["day"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_sessions_topic_id"), ["topic_id"], unique=False)


def downgrade() -> None:
    """Откатить изменения: удалить обе таблицы."""
    with op.batch_alter_table("study_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_study_sessions_topic_id"))
        batch_op.drop_index(batch_op.f("ix_study_sessions_day"))

    op.drop_table("study_sessions")
    with op.batch_alter_table("journal_entries", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_journal_entries_topic_id"))

    op.drop_table("journal_entries")
