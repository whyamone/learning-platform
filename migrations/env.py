"""Сценарий запуска миграций Alembic.

Alembic выполняет этот файл при командах вроде `alembic upgrade head`.
Задача файла — подключиться к нашей базе и сообщить Alembic,
какие таблицы описаны в коде (чтобы он мог сравнить код и базу).
"""

from logging.config import fileConfig

from alembic import context

# Импорт моделей обязателен: без него Alembic не узнает о таблицах.
import app.models  # noqa: F401
from app.config import get_settings
from app.db import Base, make_engine

config = context.config

# Настроить логи по секциям из alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Описание всех таблиц, собранное из моделей.
target_metadata = Base.metadata


def get_url() -> str:
    """Адрес базы: либо переданный явно (так делают тесты), либо из настроек."""
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    """Режим «без подключения»: не менять базу, а только напечатать SQL."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Обычный режим: подключиться к базе и применить миграции."""
    engine = make_engine(get_url())
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite почти не умеет менять готовые таблицы (ALTER TABLE).
            # «Пакетный режим» обходит это: создаёт новую таблицу и переносит данные.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
