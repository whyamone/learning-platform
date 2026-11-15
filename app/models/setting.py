"""Таблица настроек пользователя."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Setting(Base):
    """Одна настройка в виде пары «ключ — значение».

    Пример: key="start_date", value="2026-11-16".
    Здесь будут жить расписание занятий и дата начала обучения —
    то, что ты меняешь в интерфейсе, а не в файле `.env`.
    """

    __tablename__ = "settings"

    # Ключ — он же первичный ключ: двух настроек с одним именем быть не может.
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    # Значение храним текстом; сложные значения (расписание) — в формате JSON.
    value: Mapped[str] = mapped_column(Text, default="")

    def __repr__(self) -> str:
        return f"Setting(key={self.key!r}, value={self.value!r})"
