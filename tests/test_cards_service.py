"""Тесты очереди повторения карточек."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CardReview, TopicStatus
from app.services import cards as cards_service
from app.services import roadmap as roadmap_service
from app.services.importer import import_content
from app.services.sm2 import Grade

TODAY = date(2026, 3, 2)
TOMORROW = TODAY + timedelta(days=1)


@pytest.fixture
def db(db_session: Session, content_dir: Path) -> Session:
    """База с тестовой картой: у темы «Переменные» три карточки."""
    import_content(db_session, content_dir)
    return db_session


def start_topic(db: Session, slug: str = "peremennye") -> None:
    topic = roadmap_service.get_topic(db, slug)
    roadmap_service.set_topic_status(db, topic, TopicStatus.IN_PROGRESS)


def test_cards_of_not_started_topic_are_hidden(db: Session):
    queue = cards_service.get_queue(db, TODAY, new_cards_per_day=10)

    assert queue.total == 0
    assert queue.next_card is None


def test_started_topic_gives_new_cards_in_file_order(db: Session):
    start_topic(db)

    queue = cards_service.get_queue(db, TODAY, new_cards_per_day=10)

    assert [card.front_md for card in queue.new] == [
        "Что делает оператор //?",
        "Чем = отличается от ==?",
        "Какой тип у значения 3.14?",
    ]
    assert queue.due == []


def test_daily_limit_of_new_cards(db: Session):
    start_topic(db)

    queue = cards_service.get_queue(db, TODAY, new_cards_per_day=2)
    assert len(queue.new) == 2

    # Ответили на одну — сегодня осталось место ещё для одной новой.
    cards_service.grade_card(db, queue.new[0], Grade.GOOD, TODAY)
    queue = cards_service.get_queue(db, TODAY, new_cards_per_day=2)
    assert len(queue.new) == 1

    cards_service.grade_card(db, queue.new[0], Grade.GOOD, TODAY)
    assert cards_service.get_queue(db, TODAY, new_cards_per_day=2).new == []

    # На следующий день лимит новых карточек восстанавливается.
    assert len(cards_service.get_queue(db, TOMORROW, new_cards_per_day=2).new) == 1


def test_graded_card_leaves_queue_and_returns_on_due_date(db: Session):
    start_topic(db)
    card = cards_service.get_queue(db, TODAY, 10).next_card

    state = cards_service.grade_card(db, card, Grade.GOOD, TODAY)

    assert state.due_date == TOMORROW
    assert state.introduced_on == TODAY
    assert card not in cards_service.get_queue(db, TODAY, 10).new
    assert cards_service.get_queue(db, TOMORROW, 10).due == [card]


def test_due_cards_go_before_new_ones(db: Session):
    start_topic(db)
    first = cards_service.get_queue(db, TODAY, 10).next_card
    cards_service.grade_card(db, first, Grade.GOOD, TODAY)

    queue = cards_service.get_queue(db, TOMORROW, 10)

    assert queue.next_card == first
    assert len(queue.new) == 2


def test_intervals_follow_sm2(db: Session):
    start_topic(db)
    card = cards_service.get_queue(db, TODAY, 10).next_card

    day = TODAY
    intervals = []
    for _ in range(3):
        state = cards_service.grade_card(db, card, Grade.GOOD, day)
        intervals.append(state.interval_days)
        day = state.due_date

    assert intervals == [1, 6, 15]
    # Каждый ответ записан в журнал.
    assert db.scalar(select(func.count()).select_from(CardReview)) == 3


def test_forgotten_card_returns_tomorrow(db: Session):
    start_topic(db)
    card = cards_service.get_queue(db, TODAY, 10).next_card
    cards_service.grade_card(db, card, Grade.GOOD, TODAY)
    cards_service.grade_card(db, card, Grade.GOOD, TOMORROW)  # интервал стал 6 дней

    later = TOMORROW + timedelta(days=6)
    state = cards_service.grade_card(db, card, Grade.AGAIN, later)

    assert state.repetitions == 0
    assert state.due_date == later + timedelta(days=1)


def test_preview_shows_when_card_returns(db: Session):
    start_topic(db)
    card = cards_service.get_queue(db, TODAY, 10).next_card
    cards_service.grade_card(db, card, Grade.GOOD, TODAY)

    preview = cards_service.preview_intervals(card)

    assert preview[Grade.AGAIN] == "завтра"
    assert preview[Grade.GOOD] == "через 6 дн."


@pytest.mark.parametrize(
    ("days", "text"),
    [(1, "завтра"), (6, "через 6 дн."), (45, "через 2 мес."), (400, "через 1,1 г.")],
)
def test_describe_interval(days, text):
    assert cards_service.describe_interval(days) == text
