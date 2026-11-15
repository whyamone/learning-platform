"""Карточки для интервального повторения.

Три таблицы — по тому же принципу, что и у тем:

* cards        — содержимое карточки, приходит из файлов и может перезаписываться;
* card_states  — твоё расписание повторений, файлы его не трогают;
* card_reviews — журнал всех ответов (пригодится для статистики на дашборде).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services.sm2 import DEFAULT_EASE_FACTOR
from app.timeutils import utcnow

if TYPE_CHECKING:
    from app.models.roadmap import Topic


class Card(Base):
    """Карточка: вопрос на лицевой стороне, ответ на обороте."""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    # Ключ — «отпечаток» темы и текста вопроса. По нему импорт узнаёт карточку
    # при повторной загрузке файлов, чтобы не потерять расписание повторений.
    key: Mapped[str] = mapped_column(String(32), unique=True)
    position: Mapped[int] = mapped_column(default=0)
    front_md: Mapped[str] = mapped_column(Text)
    back_md: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    topic: Mapped[Topic] = relationship(back_populates="cards")
    state: Mapped[CardState | None] = relationship(
        back_populates="card", cascade="all, delete-orphan", uselist=False
    )
    reviews: Mapped[list[CardReview]] = relationship(
        back_populates="card", cascade="all, delete-orphan"
    )


class CardState(Base):
    """Расписание повторений одной карточки — числа алгоритма SM-2.

    Записи нет, пока карточку ни разу не показывали: такая карточка считается новой.
    """

    __tablename__ = "card_states"

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True
    )
    # Сколько раз подряд карточка вспомнилась успешно.
    repetitions: Mapped[int] = mapped_column(default=0)
    # Через сколько дней после прошлого показа нужно показать снова.
    interval_days: Mapped[int] = mapped_column(default=0)
    # «Лёгкость»: чем больше, тем быстрее растут интервалы.
    ease_factor: Mapped[float] = mapped_column(default=DEFAULT_EASE_FACTOR)
    # День следующего показа. index=True ускоряет поиск «что повторить сегодня».
    due_date: Mapped[date] = mapped_column(index=True)
    # День первого показа — чтобы ограничивать число новых карточек в день.
    introduced_on: Mapped[date] = mapped_column(index=True)
    last_reviewed_at: Mapped[datetime] = mapped_column(default=utcnow)

    card: Mapped[Card] = relationship(back_populates="state")


class CardReview(Base):
    """Запись журнала: когда карточку показали и как на неё ответили."""

    __tablename__ = "card_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), index=True)
    # Оценка ответа по шкале SM-2 от 0 до 5.
    quality: Mapped[int] = mapped_column()
    # Какой интервал был назначен после этого ответа.
    interval_days: Mapped[int] = mapped_column(default=0)
    reviewed_at: Mapped[datetime] = mapped_column(default=utcnow)

    card: Mapped[Card] = relationship(back_populates="reviews")
