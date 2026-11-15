"""таблицы дорожной карты: этапы, модули, темы, ссылки, прогресс

Идентификатор: f34fd6c05e7d
Предыдущая миграция: bf06533b694b
Создана: 2026-11-15 12:18:50.265460
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Служебные поля Alembic: по ним он выстраивает миграции в цепочку.
revision: str = "f34fd6c05e7d"
down_revision: str | None = "bf06533b694b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применить изменения: создать пять таблиц дорожной карты."""
    op.create_table(
        "stages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("month_from", sa.Integer(), nullable=False),
        sa.Column("month_to", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    with op.batch_alter_table("modules", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_modules_stage_id"), ["stage_id"], unique=False)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("estimated_hours", sa.Double(), nullable=False),
        sa.Column("concepts", sa.JSON(), nullable=False),
        sa.Column("glossary", sa.JSON(), nullable=False),
        sa.Column("done_criteria", sa.JSON(), nullable=False),
        sa.Column("theory_md", sa.Text(), nullable=False),
        sa.Column("practice_md", sa.Text(), nullable=False),
        sa.Column("is_stub", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("source_path", sa.String(length=300), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    with op.batch_alter_table("topics", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_topics_module_id"), ["module_id"], unique=False)

    op.create_table(
        "topic_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("lang", sa.String(length=5), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("topic_links", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_topic_links_topic_id"), ["topic_id"], unique=False)

    op.create_table(
        "topic_progress",
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("topic_id"),
    )


def downgrade() -> None:
    """Откатить изменения: удалить таблицы в обратном порядке."""
    op.drop_table("topic_progress")
    with op.batch_alter_table("topic_links", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_topic_links_topic_id"))

    op.drop_table("topic_links")
    with op.batch_alter_table("topics", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_topics_module_id"))

    op.drop_table("topics")
    with op.batch_alter_table("modules", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_modules_stage_id"))

    op.drop_table("modules")
    op.drop_table("stages")
