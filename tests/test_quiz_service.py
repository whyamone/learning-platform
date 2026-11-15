"""Тесты проверки квизов."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.services import quiz as quiz_service
from app.services import roadmap as roadmap_service
from app.services.importer import import_content


@pytest.fixture
def topic(db_session: Session, content_dir: Path):
    """Тема «Переменные» с квизом из двух вопросов."""
    import_content(db_session, content_dir)
    return roadmap_service.get_topic(db_session, "peremennye")


def test_all_answers_correct(topic):
    first, second = topic.questions

    result = quiz_service.grade_quiz(topic.questions, {first.id: 0, second.id: 1})

    assert (result.correct, result.total, result.percent) == (2, 2, 100)
    assert result.is_passed


def test_wrong_and_missing_answers(topic):
    first, second = topic.questions

    result = quiz_service.grade_quiz(topic.questions, {first.id: 2})

    assert (result.correct, result.percent) == (0, 0)
    assert not result.is_passed
    assert result.items[0].chosen_index == 2
    assert result.items[1].chosen_index is None  # на второй вопрос не ответили


def test_half_correct_is_not_passed(topic):
    first, second = topic.questions

    result = quiz_service.grade_quiz(topic.questions, {first.id: 0, second.id: 0})

    assert result.percent == 50
    assert not result.is_passed


def test_parse_answers_ignores_garbage():
    form = {"q-12": "1", "q-13": "0", "q-abc": "1", "q-14": "не число", "csrf": "x"}

    assert quiz_service.parse_answers(form) == {12: 1, 13: 0}


def test_stats_track_best_and_last_attempt(db_session: Session, topic):
    first, second = topic.questions
    assert quiz_service.get_stats(db_session, topic).attempts == 0

    perfect = quiz_service.grade_quiz(topic.questions, {first.id: 0, second.id: 1})
    half = quiz_service.grade_quiz(topic.questions, {first.id: 0})
    quiz_service.save_attempt(db_session, topic, perfect)
    quiz_service.save_attempt(db_session, topic, half)

    stats = quiz_service.get_stats(db_session, topic)
    assert (stats.attempts, stats.best_percent, stats.last_percent) == (2, 100, 50)
