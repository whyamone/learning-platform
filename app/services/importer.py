"""Импорт учебных материалов из файлов в базу данных.

Работает по принципу «обнови или создай» (по-английски upsert):

* тема с таким slug уже есть в базе → обновляем её поля;
* темы нет → создаём;
* тема есть в базе, но файла больше нет → помечаем неактивной (скрываем).

Строки в базе не удаляются и не пересоздаются, поэтому прогресс,
привязанный к теме, сохраняется при любом количестве импортов.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, Module, QuizQuestion, Stage, Topic, TopicLink
from app.services.content_loader import ContentProblem, load_content
from app.timeutils import utcnow


@dataclass
class ImportReport:
    """Итог импорта: сколько чего загружено и какие были замечания."""

    stages: int = 0
    modules: int = 0
    topics: int = 0
    questions: int = 0
    cards: int = 0
    problems: list[ContentProblem] = field(default_factory=list)
    finished_at: datetime = field(default_factory=utcnow)


def make_card_key(topic_slug: str, front: str) -> str:
    """Вычислить ключ карточки — короткий «отпечаток» темы и текста вопроса.

    Хеш-функция превращает любой текст в строку фиксированной длины: одинаковый
    текст всегда даёт одинаковый результат, а малейшее изменение — совсем другой.
    Пробелы и регистр букв не учитываем, чтобы мелкая правка не создавала новую карточку.
    """
    normalized = " ".join(front.lower().split())
    digest = hashlib.sha256(f"{topic_slug}\n{normalized}".encode()).hexdigest()
    return digest[:32]


def import_content(db: Session, content_dir: Path) -> ImportReport:
    """Прочитать папку с материалами и привести базу в соответствие с ней."""
    loaded = load_content(content_dir)
    report = ImportReport(problems=loaded.problems)

    # Загружаем всё, что уже есть в базе, в словари вида {slug: объект}.
    stages = {stage.slug: stage for stage in db.scalars(select(Stage))}
    modules = {module.slug: module for module in db.scalars(select(Module))}
    topics = {topic.slug: topic for topic in db.scalars(select(Topic))}
    cards = {card.key: card for card in db.scalars(select(Card))}

    # Сначала считаем всё неактивным. Ниже «включим» то, что нашлось в файлах.
    for item in (*stages.values(), *modules.values(), *topics.values(), *cards.values()):
        item.is_active = False

    for stage_data in loaded.stages:
        stage = stages.get(stage_data.slug)
        if stage is None:
            stage = Stage(slug=stage_data.slug)
            db.add(stage)
        stage.position = stage_data.position
        stage.title = stage_data.title
        stage.description = stage_data.description
        stage.month_from = stage_data.month_from
        stage.month_to = stage_data.month_to
        stage.is_active = True
        report.stages += 1

        for module_data in stage_data.modules:
            module = modules.get(module_data.slug)
            if module is None:
                module = Module(slug=module_data.slug)
                db.add(module)
            # Присваивание stage само проставит stage_id при сохранении.
            module.stage = stage
            module.position = module_data.position
            module.title = module_data.title
            module.description = module_data.description
            module.is_active = True
            report.modules += 1

            for topic_data in module_data.topics:
                topic = topics.get(topic_data.slug)
                if topic is None:
                    topic = Topic(slug=topic_data.slug)
                    db.add(topic)
                topic.module = module
                topic.position = topic_data.position
                topic.title = topic_data.title
                topic.summary = topic_data.summary
                topic.goal = topic_data.goal
                topic.estimated_hours = topic_data.estimated_hours
                topic.concepts = topic_data.concepts
                topic.glossary = topic_data.glossary
                topic.done_criteria = topic_data.done_criteria
                topic.theory_md = topic_data.theory_md
                topic.practice_md = topic_data.practice_md
                topic.is_stub = topic_data.is_stub
                topic.source_path = topic_data.source_path
                topic.is_active = True
                # Ссылки проще заменить целиком: старые удалятся сами
                # (см. cascade="all, delete-orphan" в модели Topic).
                topic.links = [
                    TopicLink(
                        position=number,
                        title=link.title,
                        url=link.url,
                        kind=link.kind,
                        lang=link.lang,
                    )
                    for number, link in enumerate(topic_data.links, start=1)
                ]
                report.topics += 1

                # Вопросы квиза заменяем целиком, как и ссылки: к отдельному
                # вопросу ничего не привязано (в попытках хранится только счёт).
                topic.questions = [
                    QuizQuestion(
                        position=number,
                        text=question.text,
                        options=question.options,
                        correct_index=question.correct_index,
                        explanation=question.explanation,
                    )
                    for number, question in enumerate(topic_data.questions, start=1)
                ]
                report.questions += len(topic_data.questions)

                # С карточками так нельзя: у каждой своё расписание повторений.
                # Поэтому ищем карточку по ключу и обновляем, а не пересоздаём.
                for number, card_data in enumerate(topic_data.cards, start=1):
                    key = make_card_key(topic_data.slug, card_data.front)
                    card = cards.get(key)
                    if card is None:
                        card = Card(key=key)
                        db.add(card)
                        cards[key] = card  # на случай двух одинаковых вопросов в файле
                    card.topic = topic
                    card.position = number
                    card.front_md = card_data.front
                    card.back_md = card_data.back
                    card.is_active = True
                    report.cards += 1

    # commit — зафиксировать все изменения разом. До него в базе ничего не меняется.
    db.commit()
    return report
