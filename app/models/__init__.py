"""Модели — Python-классы, которые описывают таблицы базы данных.

Все модели импортируются здесь, чтобы Alembic «увидел» их
и смог сравнить с реальной структурой базы.
"""

from app.models.card import Card, CardReview, CardState
from app.models.progress import TopicProgress, TopicStatus
from app.models.quiz import QuizAttempt, QuizQuestion
from app.models.roadmap import Module, Stage, Topic, TopicLink
from app.models.setting import Setting

__all__ = [
    "Card",
    "CardReview",
    "CardState",
    "Module",
    "QuizAttempt",
    "QuizQuestion",
    "Setting",
    "Stage",
    "Topic",
    "TopicLink",
    "TopicProgress",
    "TopicStatus",
]
