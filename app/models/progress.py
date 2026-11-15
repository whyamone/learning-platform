"""Прогресс по темам — твои личные данные.

Прогресс хранится отдельно от содержимого тем. Поэтому при повторном
импорте материалов из content/ статусы не сбрасываются.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.timeutils import utcnow

if TYPE_CHECKING:
    from app.models.roadmap import Topic


class TopicStatus(StrEnum):
    """Возможные статусы темы.

    StrEnum — перечисление: набор разрешённых значений. Опечатку вроде
    "donee" Python не пропустит, в отличие от обычной строки.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REVIEW = "review"

    @property
    def label(self) -> str:
        """Название статуса по-русски — для показа на странице."""
        return _STATUS_LABELS[self]

    @property
    def is_completed(self) -> bool:
        """Считается ли тема пройденной.

        «Повторить» тоже считается: тема изучена, просто к ней стоит вернуться.
        Иначе пометка «повторить» уменьшала бы процент — как наказание за честность.
        """
        return self in (TopicStatus.DONE, TopicStatus.REVIEW)


_STATUS_LABELS = {
    TopicStatus.NOT_STARTED: "Не начато",
    TopicStatus.IN_PROGRESS: "В процессе",
    TopicStatus.DONE: "Готово",
    TopicStatus.REVIEW: "Повторить",
}


class TopicProgress(Base):
    """Статус одной темы и даты, когда она была начата и завершена."""

    __tablename__ = "topic_progress"

    # Номер темы — одновременно первичный ключ: на тему приходится одна запись.
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), default=TopicStatus.NOT_STARTED.value)
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    # onupdate: дата обновляется сама при каждом изменении записи.
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    topic: Mapped[Topic] = relationship(back_populates="progress")
