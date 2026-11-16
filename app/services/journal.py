"""Журнал: заметки и ссылки к темам."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import JournalEntry, Topic

MAX_TEXT_LENGTH = 5000


class JournalError(Exception):
    """Ошибка в записи журнала. Текст показывается пользователю."""


def add_entry(db: Session, topic: Topic, text: str, url: str) -> JournalEntry:
    """Добавить запись к теме. Нужен текст, ссылка или и то и другое."""
    text = text.strip()
    url = url.strip()

    if not text and not url:
        raise JournalError("Напиши заметку или вставь ссылку.")
    if len(text) > MAX_TEXT_LENGTH:
        raise JournalError(f"Заметка длиннее {MAX_TEXT_LENGTH} символов.")
    # Разрешаем только обычные веб-адреса. Иначе в поле можно было бы вставить
    # «ссылку» вида javascript:..., которая выполняет код при нажатии.
    if url and not url.startswith(("http://", "https://")):
        raise JournalError("Ссылка должна начинаться с http:// или https://.")

    entry = JournalEntry(topic=topic, text=text, url=url)
    db.add(entry)
    db.commit()
    return entry


def get_entry(db: Session, entry_id: int) -> JournalEntry | None:
    return db.get(JournalEntry, entry_id)


def delete_entry(db: Session, entry: JournalEntry) -> None:
    db.delete(entry)
    db.commit()


def list_all(db: Session, limit: int = 200) -> list[JournalEntry]:
    """Все записи журнала, новые сверху."""
    query = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.topic))
        .order_by(JournalEntry.created_at.desc(), JournalEntry.id.desc())
        .limit(limit)
    )
    return list(db.scalars(query))
