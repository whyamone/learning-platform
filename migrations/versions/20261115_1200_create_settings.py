"""создать таблицу настроек

Идентификатор: bf06533b694b
Предыдущая миграция: нет (это первая)
Создана: 2026-11-15 12:00:22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Служебные поля Alembic: по ним он выстраивает миграции в цепочку.
revision: str = "bf06533b694b"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применить изменения: создать таблицу settings."""
    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Откатить изменения: удалить таблицу settings."""
    op.drop_table("settings")
