"""${message}

Идентификатор: ${up_revision}
Предыдущая миграция: ${down_revision | comma,n}
Создана: ${create_date}
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

# Служебные поля Alembic: по ним он выстраивает миграции в цепочку.
revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Применить изменения."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Откатить изменения."""
    ${downgrades if downgrades else "pass"}
