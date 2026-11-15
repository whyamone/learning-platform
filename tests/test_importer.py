"""Тесты импорта материалов в базу данных."""

from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Card, Module, QuizQuestion, Stage, Topic, TopicLink, TopicStatus
from app.services import cards as cards_service
from app.services import roadmap as roadmap_service
from app.services.importer import import_content
from app.services.sm2 import Grade
from tests.helpers import SIMPLE_TOPIC, write_file


def count(db: Session, model) -> int:
    """Сколько строк в таблице."""
    return db.scalar(select(func.count()).select_from(model))


def test_import_creates_rows(db_session: Session, content_dir: Path):
    report = import_content(db_session, content_dir)

    assert (report.stages, report.modules, report.topics) == (1, 2, 3)
    assert report.problems == []
    assert count(db_session, Stage) == 1
    assert count(db_session, Module) == 2
    assert count(db_session, Topic) == 3
    assert count(db_session, TopicLink) == 1


def test_import_twice_does_not_duplicate(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    import_content(db_session, content_dir)

    assert count(db_session, Topic) == 3
    assert count(db_session, TopicLink) == 1


def test_reimport_updates_text_and_keeps_progress(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    topic = roadmap_service.get_topic(db_session, "usloviya")
    roadmap_service.set_topic_status(db_session, topic, TopicStatus.DONE)

    # Правим файл темы и импортируем заново.
    path = content_dir / "01-fundament" / "01-python" / "02-usloviya.md"
    write_file(path, SIMPLE_TOPIC.format(title="Условия if и else"))
    import_content(db_session, content_dir)

    topic = roadmap_service.get_topic(db_session, "usloviya")
    assert topic.title == "Условия if и else"
    assert topic.status == TopicStatus.DONE


def test_removed_topic_is_hidden_and_restored_with_progress(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    topic = roadmap_service.get_topic(db_session, "terminal")
    roadmap_service.set_topic_status(db_session, topic, TopicStatus.IN_PROGRESS)
    path = content_dir / "01-fundament" / "02-linux" / "01-terminal.md"
    original_text = path.read_text(encoding="utf-8")

    # Удаляем файл: тема должна исчезнуть с карты, но остаться в базе.
    path.unlink()
    import_content(db_session, content_dir)
    assert roadmap_service.get_topic(db_session, "terminal") is None
    assert count(db_session, Topic) == 3

    # Возвращаем файл: тема возвращается вместе со статусом.
    write_file(path, original_text)
    import_content(db_session, content_dir)
    assert roadmap_service.get_topic(db_session, "terminal").status == TopicStatus.IN_PROGRESS


def test_topic_moved_to_another_module_keeps_progress(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    topic = roadmap_service.get_topic(db_session, "usloviya")
    roadmap_service.set_topic_status(db_session, topic, TopicStatus.REVIEW)

    old_path = content_dir / "01-fundament" / "01-python" / "02-usloviya.md"
    new_path = content_dir / "01-fundament" / "02-linux" / "02-usloviya.md"
    old_path.rename(new_path)
    import_content(db_session, content_dir)

    topic = roadmap_service.get_topic(db_session, "usloviya")
    assert topic.module.slug == "linux"
    assert topic.status == TopicStatus.REVIEW


def test_problems_are_returned_in_report(db_session: Session, content_dir: Path):
    write_file(content_dir / "01-fundament" / "01-python" / "03-plohaya.md", "без шапки")

    report = import_content(db_session, content_dir)

    assert report.topics == 3
    assert len(report.problems) == 1


# --- Квизы и карточки -----------------------------------------------------------


def test_import_creates_questions_and_cards(db_session: Session, content_dir: Path):
    report = import_content(db_session, content_dir)

    assert (report.questions, report.cards) == (2, 3)
    topic = roadmap_service.get_topic(db_session, "peremennye")
    assert [question.correct_index for question in topic.questions] == [0, 1]
    assert len(topic.active_cards) == 3


def test_reimport_does_not_duplicate_questions_and_cards(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    import_content(db_session, content_dir)

    assert count(db_session, QuizQuestion) == 2
    assert count(db_session, Card) == 3


def test_editing_card_answer_keeps_schedule(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    topic = roadmap_service.get_topic(db_session, "peremennye")
    roadmap_service.set_topic_status(db_session, topic, TopicStatus.IN_PROGRESS)
    card = topic.active_cards[0]
    cards_service.grade_card(db_session, card, Grade.GOOD, date(2026, 3, 2))

    # Меняем оборот первой карточки и убираем третью.
    path = content_dir / "01-fundament" / "01-python" / "01-peremennye.cards.yaml"
    write_file(
        path,
        "- front: Что делает оператор //?\n  back: Новый текст ответа.\n"
        "- front: Чем = отличается от ==?\n  back: Первый присваивает, второй сравнивает.\n",
    )
    import_content(db_session, content_dir)

    topic = roadmap_service.get_topic(db_session, "peremennye")
    assert len(topic.active_cards) == 2
    assert topic.active_cards[0].back_md == "Новый текст ответа."
    assert topic.active_cards[0].state.due_date == date(2026, 3, 3)  # расписание на месте
    assert count(db_session, Card) == 3  # убранная карточка скрыта, но не удалена
