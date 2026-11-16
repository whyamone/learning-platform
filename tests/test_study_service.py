"""Тесты учёта времени и журнала."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.services import journal as journal_service
from app.services import roadmap as roadmap_service
from app.services import study as study_service
from app.services.importer import import_content

TODAY = date(2026, 3, 4)
START = datetime(2026, 3, 4, 15, 30)


@pytest.fixture
def db(db_session: Session, content_dir: Path) -> Session:
    import_content(db_session, content_dir)
    return db_session


def test_timer_records_elapsed_minutes(db: Session):
    topic = roadmap_service.get_topic(db, "peremennye")

    study_service.start_timer(db, topic, START, TODAY)
    assert study_service.get_running(db) is not None

    session = study_service.stop_timer(db, START + timedelta(minutes=47, seconds=30))

    assert session.minutes == 47
    assert session.topic.slug == "peremennye"
    assert session.day == TODAY
    assert study_service.get_running(db) is None


def test_forgotten_timer_is_capped(db: Session):
    study_service.start_timer(db, None, START, TODAY)

    session = study_service.stop_timer(db, START + timedelta(hours=14))

    assert session.minutes == study_service.MAX_TIMER_MINUTES


def test_accidental_click_is_not_recorded(db: Session):
    study_service.start_timer(db, None, START, TODAY)
    study_service.stop_timer(db, START + timedelta(seconds=20))

    assert study_service.list_recent(db) == []


def test_starting_new_timer_stops_previous_one(db: Session):
    study_service.start_timer(db, None, START, TODAY)
    study_service.start_timer(db, None, START + timedelta(minutes=30), TODAY)

    finished = study_service.list_recent(db)
    assert [session.minutes for session in finished] == [30]
    assert study_service.get_running(db) is not None


def test_stop_without_running_timer_does_nothing(db: Session):
    assert study_service.stop_timer(db, START) is None


def test_manual_entry_and_correction(db: Session):
    session = study_service.add_manual(db, TODAY, 90, None, today=TODAY)
    study_service.update_minutes(db, session, 60)

    assert study_service.list_recent(db)[0].minutes == 60

    study_service.delete_session(db, session)
    assert study_service.list_recent(db) == []


@pytest.mark.parametrize("minutes", [0, -5, 5000])
def test_manual_entry_rejects_bad_minutes(db: Session, minutes):
    with pytest.raises(study_service.StudyError):
        study_service.add_manual(db, TODAY, minutes, None, today=TODAY)


def test_manual_entry_rejects_future_date(db: Session):
    with pytest.raises(study_service.StudyError):
        study_service.add_manual(db, TODAY + timedelta(days=1), 60, None, today=TODAY)


# --- Журнал ----------------------------------------------------------------------


def test_journal_entry_with_note_and_link(db: Session):
    topic = roadmap_service.get_topic(db, "peremennye")

    journal_service.add_entry(db, topic, "  Решил задачи 1–3  ", "https://github.com/me/study")

    entry = journal_service.list_all(db)[0]
    assert entry.text == "Решил задачи 1–3"
    assert entry.url == "https://github.com/me/study"
    assert topic.journal_entries == [entry]


def test_journal_rejects_empty_entry(db: Session):
    topic = roadmap_service.get_topic(db, "peremennye")

    with pytest.raises(journal_service.JournalError):
        journal_service.add_entry(db, topic, "   ", "")


@pytest.mark.parametrize("url", ["javascript:alert(1)", "github.com/me", "ftp://host/file"])
def test_journal_rejects_unsafe_links(db: Session, url):
    topic = roadmap_service.get_topic(db, "peremennye")

    with pytest.raises(journal_service.JournalError):
        journal_service.add_entry(db, topic, "заметка", url)
