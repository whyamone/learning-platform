"""Модели — Python-классы, которые описывают таблицы базы данных.

Все модели импортируются здесь, чтобы Alembic «увидел» их
и смог сравнить с реальной структурой базы.
"""

from app.models.progress import TopicProgress, TopicStatus
from app.models.roadmap import Module, Stage, Topic, TopicLink
from app.models.setting import Setting

__all__ = [
    "Module",
    "Setting",
    "Stage",
    "Topic",
    "TopicLink",
    "TopicProgress",
    "TopicStatus",
]
