"""Тесты расчётов дашборда: неделя, серия дней, темп, прогноз."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models import StudySession, TopicStatus
from app.services import dashboard as dashboard_service
from app.services import roadmap as roadmap_service
from app.services.dashboard import Pace, calculate_streak, forecast_dates, week_start
from app.services.importer import import_content

# Среда. Неделя: понедельник 2 марта — воскресенье 8 марта 2026 года.
TODAY = date(2026, 3, 4)
MONDAY = date(2026, 3, 2)


def days_ago(count: int) -> date:
    return TODAY - timedelta(days=count)


def add_session(db: Session, day: date, minutes: int) -> None:
    db.add(StudySession(day=day, minutes=minutes, source="manual"))
    db.commit()


# --- Чистые функции ---------------------------------------------------------------


def test_week_starts_on_monday():
    assert week_start(TODAY) == MONDAY
    assert week_start(MONDAY) == MONDAY
    assert week_start(date(2026, 3, 8)) == MONDAY  # воскресенье — та же неделя


def test_streak_counts_consecutive_days_including_today():
    streak = calculate_streak([days_ago(2), days_ago(1), TODAY], TODAY)

    assert (streak.current, streak.best, streak.studied_today) == (3, 3, True)


def test_streak_survives_until_the_day_ends():
    # Сегодня ещё не занимался, но вчера и позавчера — да: серия не оборвана.
    streak = calculate_streak([days_ago(2), days_ago(1)], TODAY)

    assert (streak.current, streak.studied_today) == (2, False)


def test_streak_breaks_after_a_missed_day():
    streak = calculate_streak([days_ago(5), days_ago(4), days_ago(3)], TODAY)

    assert streak.current == 0
    assert streak.best == 3  # лучшая серия при этом сохраняется


def test_streak_without_any_activity():
    streak = calculate_streak([], TODAY)

    assert (streak.current, streak.best) == (0, 0)


def test_forecast_accumulates_hours_across_stages():
    # 23 часа при темпе 11,5 ч в неделю — это две недели; ещё 46 часов — ещё четыре.
    dates = forecast_dates([23, 46], hours_per_week=11.5, today=TODAY)

    assert dates == [TODAY + timedelta(weeks=2), TODAY + timedelta(weeks=6)]


def test_forecast_slower_pace_gives_later_date():
    fast = forecast_dates([40], hours_per_week=10, today=TODAY)[0]
    slow = forecast_dates([40], hours_per_week=5, today=TODAY)[0]

    assert slow - TODAY == 2 * (fast - TODAY)


def test_forecast_with_zero_pace_has_no_date():
    assert forecast_dates([40], hours_per_week=0, today=TODAY) == [None]


# --- Функции, работающие с базой --------------------------------------------------


def test_week_sums_minutes_by_day(db_session: Session):
    add_session(db_session, MONDAY, 60)
    add_session(db_session, MONDAY, 30)
    add_session(db_session, TODAY, 120)
    add_session(db_session, days_ago(10), 500)  # прошлая неделя — не считается

    week = dashboard_service.get_week(db_session, TODAY, goal_hours=10)

    assert [day.minutes for day in week.days] == [90, 0, 120, 0, 0, 0, 0]
    assert [day.name for day in week.days][0] == "Пн"
    assert week.total_minutes == 210
    assert week.goal_percent == 35  # 210 минут из 600
    assert week.days[2].is_today
    assert week.days[3].is_future
    assert week.days[2].height_percent == 100  # самый высокий столбец


def test_week_goal_percent_is_capped(db_session: Session):
    add_session(db_session, TODAY, 600)

    assert dashboard_service.get_week(db_session, TODAY, goal_hours=1).goal_percent == 100


def test_pace_falls_back_to_goal_without_data(db_session: Session):
    pace = dashboard_service.get_pace(db_session, TODAY, goal_hours=11.5)

    assert pace == Pace(hours_per_week=11.5, is_measured=False)


def test_pace_is_not_measured_in_first_two_weeks(db_session: Session):
    # Одно занятие в первый день не должно превращаться в «темп 2 часа в неделю».
    add_session(db_session, days_ago(6), 120)

    pace = dashboard_service.get_pace(db_session, TODAY, goal_hours=11.5)

    assert pace == Pace(hours_per_week=11.5, is_measured=False)


def test_pace_after_three_weeks_uses_elapsed_time(db_session: Session):
    # Занимаешься ровно три недели (21 день), записано 9 часов: темп — 3 часа в неделю.
    add_session(db_session, days_ago(20), 270)
    add_session(db_session, TODAY, 270)

    pace = dashboard_service.get_pace(db_session, TODAY, goal_hours=11.5)

    assert pace.is_measured
    assert pace.hours_per_week == pytest.approx(3.0)


def test_pace_uses_last_four_weeks_only(db_session: Session):
    add_session(db_session, days_ago(100), 6000)  # давно — не учитывается
    add_session(db_session, days_ago(20), 240)
    add_session(db_session, TODAY, 240)

    pace = dashboard_service.get_pace(db_session, TODAY, goal_hours=11.5)

    assert pace.hours_per_week == pytest.approx(2.0)  # 8 часов за 4 недели


def test_forecast_shrinks_when_topic_is_done(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    pace = Pace(hours_per_week=6.5, is_measured=True)

    before = dashboard_service.get_forecast(roadmap_service.get_stages(db_session), pace, TODAY)
    assert before[0].remaining_hours == 6.5  # 2,5 + 2 + 2 часа
    assert before[0].finish_date == TODAY + timedelta(weeks=1)

    topic = roadmap_service.get_topic(db_session, "peremennye")
    roadmap_service.set_topic_status(db_session, topic, TopicStatus.DONE)
    after = dashboard_service.get_forecast(roadmap_service.get_stages(db_session), pace, TODAY)

    assert after[0].remaining_hours == 4.0
    assert after[0].finish_date < before[0].finish_date


def test_finished_stage_has_no_forecast_date(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    for slug in ("peremennye", "usloviya", "terminal"):
        topic = roadmap_service.get_topic(db_session, slug)
        roadmap_service.set_topic_status(db_session, topic, TopicStatus.DONE)

    forecast = dashboard_service.get_forecast(
        roadmap_service.get_stages(db_session), Pace(10, True), TODAY
    )

    assert forecast[0].finish_date is None
