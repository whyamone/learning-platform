"""Твоя учебная активность: занятия (учёт времени) и журнал."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.timeutils import utcnow

if TYPE_CHECKING:
    from app.models.roadmap import Topic


class StudySession(Base):
    """Одно занятие: сколько минут и над какой темой.

    Запись создаётся двумя способами: таймером (кнопки «Начать» и «Закончить»)
    или вручную, если таймер забыл включить.
    """

    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Тема необязательна: можно заниматься и «вообще». SET NULL — если тему
    # удалят из базы, занятие останется, просто без привязки.
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), index=True, default=None
    )
    # День занятия по местному времени — по нему строятся неделя и серия дней.
    day: Mapped[date] = mapped_column(index=True)
    minutes: Mapped[int] = mapped_column(default=0)
    # "timer" или "manual".
    source: Mapped[str] = mapped_column(String(10), default="manual")
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    # Пока таймер идёт, времени окончания нет (None).
    ended_at: Mapped[datetime | None] = mapped_column(default=None)

    topic: Mapped[Topic | None] = relationship()

    @property
    def is_running(self) -> bool:
        return self.source == "timer" and self.ended_at is None


class JournalEntry(Base):
    """Запись журнала к теме: заметка, ссылка на репозиторий или решённую задачу."""

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    # Ссылка необязательна: запись может быть просто заметкой.
    url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    topic: Mapped[Topic] = relationship(back_populates="journal_entries")
