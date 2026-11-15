"""квизы и карточки: вопросы, попытки, карточки, расписание, журнал ответов

Идентификатор: c4a7b790cc9a
Предыдущая миграция: f34fd6c05e7d
Создана: 2026-11-15 17:32:12.656438
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Служебные поля Alembic: по ним он выстраивает миграции в цепочку.
revision: str = "c4a7b790cc9a"
down_revision: str | None = "f34fd6c05e7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применить изменения: создать пять таблиц для квизов и карточек."""
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("front_md", sa.Text(), nullable=False),
        sa.Column("back_md", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    with op.batch_alter_table("cards", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cards_topic_id"), ["topic_id"], unique=False)

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("quiz_attempts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_quiz_attempts_topic_id"), ["topic_id"], unique=False)

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("quiz_questions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_quiz_questions_topic_id"), ["topic_id"], unique=False)

    op.create_table(
        "card_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("card_reviews", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_card_reviews_card_id"), ["card_id"], unique=False)

    op.create_table(
        "card_states",
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("ease_factor", sa.Double(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("introduced_on", sa.Date(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("card_id"),
    )
    with op.batch_alter_table("card_states", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_card_states_due_date"), ["due_date"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_card_states_introduced_on"), ["introduced_on"], unique=False
        )


def downgrade() -> None:
    """Откатить изменения: удалить таблицы в обратном порядке."""
    with op.batch_alter_table("card_states", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_card_states_introduced_on"))
        batch_op.drop_index(batch_op.f("ix_card_states_due_date"))

    op.drop_table("card_states")
    with op.batch_alter_table("card_reviews", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_card_reviews_card_id"))

    op.drop_table("card_reviews")
    with op.batch_alter_table("quiz_questions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_quiz_questions_topic_id"))

    op.drop_table("quiz_questions")
    with op.batch_alter_table("quiz_attempts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_quiz_attempts_topic_id"))

    op.drop_table("quiz_attempts")
    with op.batch_alter_table("cards", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cards_topic_id"))

    op.drop_table("cards")
