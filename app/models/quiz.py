"""Квизы: вопросы к темам и история попыток."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.timeutils import utcnow

if TYPE_CHECKING:
    from app.models.roadmap import Topic


class QuizQuestion(Base):
    """Вопрос с вариантами ответа. Приходит из файла «<тема>.quiz.yaml»."""

    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text)
    # Варианты ответа — список строк в формате JSON.
    options: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Номер правильного варианта. Внутри программы счёт идёт с нуля,
    # хотя в файле для удобства человека он пишется с единицы.
    correct_index: Mapped[int] = mapped_column(default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")

    topic: Mapped[Topic] = relationship(back_populates="questions")


class QuizAttempt(Base):
    """Одна попытка пройти квиз: сколько ответов верных из скольких."""

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    correct_count: Mapped[int] = mapped_column(default=0)
    total_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    topic: Mapped[Topic] = relationship(back_populates="quiz_attempts")

    @property
    def percent(self) -> int:
        if self.total_count == 0:
            return 0
        return round(self.correct_count * 100 / self.total_count)
