"""Учёт времени занятий: таймер и ручной ввод."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import StudySession, Topic

# Если таймер забыли остановить, засчитываем не больше этого времени.
# Пять часов подряд без перерыва не занимается почти никто.
MAX_TIMER_MINUTES = 300
# Разумные границы для ручного ввода.
MAX_MANUAL_MINUTES = 16 * 60


class StudyError(Exception):
    """Ошибка учёта времени. Текст показывается пользователю."""


def get_running(db: Session) -> StudySession | None:
    """Вернуть идущее сейчас занятие или None, если таймер не запущен."""
    query = (
        select(StudySession)
        .where(StudySession.source == "timer", StudySession.ended_at.is_(None))
        .options(selectinload(StudySession.topic))
        .order_by(StudySession.started_at.desc())
    )
    return db.scalars(query).first()


def elapsed_minutes(session: StudySession, now: datetime) -> int:
    """Сколько минут прошло с начала занятия."""
    seconds = (now - session.started_at).total_seconds()
    return max(0, int(seconds // 60))


def start_timer(db: Session, topic: Topic | None, now: datetime, today: date) -> StudySession:
    """Запустить таймер. Если он уже идёт — сначала остановить прежний."""
    stop_timer(db, now)

    session = StudySession(topic=topic, day=today, source="timer", started_at=now, minutes=0)
    db.add(session)
    db.commit()
    return session


def stop_timer(db: Session, now: datetime) -> StudySession | None:
    """Остановить таймер и записать длительность. Вернуть завершённое занятие."""
    session = get_running(db)
    if session is None:
        return None

    minutes = min(elapsed_minutes(session, now), MAX_TIMER_MINUTES)
    session.ended_at = now
    # Меньше минуты считаем случайным нажатием и не засчитываем.
    session.minutes = minutes
    if minutes == 0:
        db.delete(session)
    db.commit()
    return session


def validate_minutes(minutes: int) -> int:
    """Проверить число минут из формы."""
    if not 1 <= minutes <= MAX_MANUAL_MINUTES:
        raise StudyError(f"Минут должно быть от 1 до {MAX_MANUAL_MINUTES}.")
    return minutes


def add_manual(
    db: Session, day: date, minutes: int, topic: Topic | None, today: date
) -> StudySession:
    """Добавить занятие вручную."""
    validate_minutes(minutes)
    if day > today:
        raise StudyError("Нельзя записать занятие на будущую дату.")

    session = StudySession(topic=topic, day=day, minutes=minutes, source="manual")
    db.add(session)
    db.commit()
    return session


def get_session(db: Session, session_id: int) -> StudySession | None:
    return db.get(StudySession, session_id)


def update_minutes(db: Session, session: StudySession, minutes: int) -> None:
    """Исправить длительность занятия — например, если таймер работал лишнее."""
    session.minutes = validate_minutes(minutes)
    db.commit()


def delete_session(db: Session, session: StudySession) -> None:
    db.delete(session)
    db.commit()


def list_recent(db: Session, limit: int = 50) -> list[StudySession]:
    """Последние завершённые занятия, новые сверху."""
    query = (
        select(StudySession)
        .where(StudySession.minutes > 0)
        .options(selectinload(StudySession.topic))
        .order_by(StudySession.day.desc(), StudySession.id.desc())
        .limit(limit)
    )
    return list(db.scalars(query))
