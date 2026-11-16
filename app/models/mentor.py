"""История разговоров с ИИ-наставником."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.timeutils import utcnow

if TYPE_CHECKING:
    from app.models.roadmap import Topic


class MentorMessage(Base):
    """Одно сообщение в чате: твоё или ответ модели.

    У каждой темы и каждого режима свой отдельный разговор.
    """

    __tablename__ = "mentor_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    # Режим: explain, review или interview.
    mode: Mapped[str] = mapped_column(String(20))
    # Кто автор: "user" — ты, "assistant" — модель. Названия такие же, как в API моделей.
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    topic: Mapped[Topic] = relationship()
