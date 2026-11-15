"""Тесты логики дорожной карты: прогресс, статусы, соседние темы."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models import TopicStatus
from app.services import roadmap as roadmap_service
from app.services.importer import import_content
from app.services.roadmap import Progress


@pytest.fixture
def db(db_session: Session, content_dir: Path) -> Session:
    """База, в которую уже загружена тестовая карта из трёх тем."""
    import_content(db_session, content_dir)
    return db_session


def set_status(db: Session, slug: str, status: TopicStatus) -> None:
    roadmap_service.set_topic_status(db, roadmap_service.get_topic(db, slug), status)


def test_progress_percent():
    assert Progress(done=1, total=3).percent == 33
    assert Progress(done=3, total=3).percent == 100
    # Пустой этап не должен вызывать деление на ноль.
    assert Progress(done=0, total=0).percent == 0


def test_new_topic_is_not_started(db: Session):
    assert roadmap_service.get_topic(db, "peremennye").status == TopicStatus.NOT_STARTED


def test_done_and_review_count_as_completed(db: Session):
    set_status(db, "peremennye", TopicStatus.DONE)
    set_status(db, "usloviya", TopicStatus.REVIEW)
    set_status(db, "terminal", TopicStatus.IN_PROGRESS)

    stage = roadmap_service.get_stages(db)[0]

    assert roadmap_service.count_progress(stage.active_topics) == Progress(done=2, total=3)


def test_status_dates(db: Session):
    topic = roadmap_service.get_topic(db, "peremennye")

    roadmap_service.set_topic_status(db, topic, TopicStatus.IN_PROGRESS)
    started_at = topic.progress.started_at
    assert started_at is not None
    assert topic.progress.completed_at is None

    roadmap_service.set_topic_status(db, topic, TopicStatus.DONE)
    assert topic.progress.started_at == started_at  # дата начала не перезаписывается
    assert topic.progress.completed_at is not None

    roadmap_service.set_topic_status(db, topic, TopicStatus.REVIEW)
    assert topic.progress.completed_at is not None  # «повторить» не отменяет завершение

    roadmap_service.set_topic_status(db, topic, TopicStatus.NOT_STARTED)
    assert topic.progress.started_at is None
    assert topic.progress.completed_at is None


def test_next_topic_prefers_in_progress(db: Session):
    stages = roadmap_service.get_stages(db)
    assert roadmap_service.get_next_topic(stages).slug == "peremennye"

    set_status(db, "terminal", TopicStatus.IN_PROGRESS)
    assert roadmap_service.get_next_topic(roadmap_service.get_stages(db)).slug == "terminal"


def test_next_topic_is_none_when_everything_is_done(db: Session):
    for slug in ("peremennye", "usloviya", "terminal"):
        set_status(db, slug, TopicStatus.DONE)

    assert roadmap_service.get_next_topic(roadmap_service.get_stages(db)) is None


def test_neighbors_cross_module_border(db: Session):
    stages = roadmap_service.get_stages(db)

    first = roadmap_service.get_neighbors(stages, roadmap_service.get_topic(db, "peremennye"))
    assert first.previous is None
    assert first.next.slug == "usloviya"

    # «Условия» — последняя тема модуля Python, следующая — первая тема модуля Linux.
    middle = roadmap_service.get_neighbors(stages, roadmap_service.get_topic(db, "usloviya"))
    assert middle.previous.slug == "peremennye"
    assert middle.next.slug == "terminal"

    last = roadmap_service.get_neighbors(stages, roadmap_service.get_topic(db, "terminal"))
    assert last.next is None
