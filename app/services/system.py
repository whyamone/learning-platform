"""Проверки состояния системы."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def database_is_available(db: Session) -> bool:
    """Проверить, отвечает ли база данных.

    Выполняем самый простой запрос `SELECT 1`. Если база недоступна,
    SQLAlchemy выбросит исключение — ловим его и возвращаем False.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True
