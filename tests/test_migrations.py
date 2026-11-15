"""Тесты миграций базы данных.

Проверяем две вещи:
1. миграции применяются к пустой базе без ошибок;
2. после миграций база совпадает с моделями в коде. Если ты изменил
   модель и забыл создать миграцию (`make migration`), этот тест упадёт.
"""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

import app.models  # noqa: F401
from app.config import BASE_DIR
from app.db import Base, make_engine


def make_alembic_config(database_url: str) -> Config:
    """Настройки Alembic, направленные на указанную (временную) базу."""
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_apply_to_empty_database(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migrations.db'}"

    command.upgrade(make_alembic_config(database_url), "head")

    engine = make_engine(database_url)
    tables = inspect(engine).get_table_names()
    engine.dispose()
    assert "settings" in tables


def test_models_match_migrations(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migrations.db'}"
    command.upgrade(make_alembic_config(database_url), "head")

    engine = make_engine(database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, Base.metadata)
    engine.dispose()

    assert differences == [], f"Модели изменились, а миграции нет: {differences}"
