"""Тесты планировщика и расписания."""

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.models import StudySession, TopicStatus
from app.services import planner as planner_service
from app.services import roadmap as roadmap_service
from app.services import schedule as schedule_service
from app.services.importer import import_content
from app.services.planner import PlanTopic, build_plan

# Понедельник 2 марта 2026 года.
MONDAY = date(2026, 3, 2)
WEDNESDAY = MONDAY + timedelta(days=2)
SCHEDULE = schedule_service.DEFAULT_SCHEDULE  # Пн 2 ч, Ср 2 ч, Чт 2 ч, Сб 3,5 ч, Вс 2 ч


def topic(name: str, minutes: int, kind: str = "study") -> PlanTopic:
    """Тема-заготовка: планировщику от темы нужно только название."""
    return PlanTopic(SimpleNamespace(title=name, slug=name), minutes, kind)


def titles(day) -> list[tuple[str, int]]:
    """Пункты дня в виде (название, минуты) — так удобнее сравнивать."""
    return [(item.topic.title if item.topic else "карточки", item.minutes) for item in day.items]


def plan(today=MONDAY, topics=(), studied=None, cards=False, schedule=SCHEDULE):
    return build_plan(today, schedule, list(topics), studied or {}, include_cards=cards)


# --- Раскладка тем ----------------------------------------------------------------


def test_topics_fill_days_according_to_schedule():
    week = plan(topics=[topic("A", 120), topic("B", 120)])[0]

    assert titles(week.days[0]) == [("A", 120)]  # понедельник
    assert week.days[1].items == []  # вторник — выходной
    assert week.days[1].is_rest
    assert titles(week.days[2]) == [("B", 120)]  # среда


def test_long_topic_is_split_across_days():
    week = plan(topics=[topic("A", 300)])[0]

    monday, wednesday, thursday = week.days[0], week.days[2], week.days[3]
    assert titles(monday) == [("A", 120)]
    assert titles(wednesday) == [("A", 120)]
    assert titles(thursday) == [("A", 60)]
    assert not monday.items[0].is_final
    assert wednesday.items[0].is_continuation
    assert thursday.items[0].is_final


def test_several_short_topics_share_one_day():
    monday = plan(topics=[topic("A", 45), topic("B", 45), topic("C", 60)])[0].days[0]

    assert titles(monday) == [("A", 45), ("B", 45), ("C", 30)]


def test_tiny_leftover_is_not_moved_to_next_day():
    # 130 минут при двух часах в расписании: десять минут хвоста не переносим.
    week = plan(topics=[topic("A", 130), topic("B", 60)])[0]

    assert titles(week.days[0]) == [("A", 120)]
    assert week.days[0].items[0].is_final
    assert titles(week.days[2])[0] == ("B", 60)


def test_cards_take_first_ten_minutes_of_each_study_day():
    week = plan(topics=[topic("A", 600)], cards=True)[0]

    assert titles(week.days[0]) == [("карточки", 10), ("A", 110)]
    assert week.days[1].items == []  # в выходной карточки не ставим


def test_revise_topics_are_marked():
    monday = plan(topics=[topic("Старая", 30, "revise"), topic("Новая", 120)])[0].days[0]

    assert [item.kind for item in monday.items] == ["revise", "study"]
    assert titles(monday) == [("Старая", 30), ("Новая", 90)]


def test_plan_covers_two_weeks():
    weeks = plan(topics=[topic("A", 2000)])

    assert [week.title for week in weeks] == ["Эта неделя", "Следующая неделя"]
    assert len(weeks[1].days) == 7
    assert weeks[0].scheduled_minutes == 690  # 11,5 часа


# --- Пропуски и уже сделанное ------------------------------------------------------


def test_missed_day_just_shifts_topics():
    """Главное свойство: пропуск не оставляет «долга», темы просто сдвигаются."""
    topics = [topic("A", 120), topic("B", 120)]

    on_monday = plan(today=MONDAY, topics=topics)[0]
    # Понедельник пропущен, открываем план в среду — тема A всё ещё первая.
    on_wednesday = plan(today=WEDNESDAY, topics=topics)[0]

    assert titles(on_monday.days[0]) == [("A", 120)]
    assert on_wednesday.days[0].items == []  # прошлое не планируем
    assert on_wednesday.days[0].is_past
    assert titles(on_wednesday.days[2]) == [("A", 120)]
    assert titles(on_wednesday.days[3]) == [("B", 120)]


def test_past_days_show_only_what_was_done():
    week = plan(today=WEDNESDAY, topics=[topic("A", 600)], studied={MONDAY: 90})[0]

    assert week.days[0].studied_minutes == 90
    assert week.days[0].items == []
    assert week.studied_minutes == 90


def test_today_plans_only_remaining_time():
    week = plan(today=MONDAY, topics=[topic("A", 600)], studied={MONDAY: 80})[0]

    assert titles(week.days[0]) == [("A", 40)]  # из двух часов осталось сорок минут


def test_today_is_done_when_schedule_is_fulfilled():
    week = plan(today=MONDAY, topics=[topic("A", 600)], studied={MONDAY: 150})[0]

    assert week.days[0].items == []
    assert titles(week.days[2]) == [("A", 120)]


def test_no_topics_left():
    week = plan(topics=[])[0]

    assert all(day.items == [] for day in week.days)


def test_find_today_and_next_study_day():
    weeks = plan(today=MONDAY + timedelta(days=1), topics=[topic("A", 600)])  # вторник

    assert planner_service.find_today(weeks).is_rest
    assert planner_service.find_next_study_day(weeks).day == WEDNESDAY


# --- Очередь тем из базы -----------------------------------------------------------


def test_queue_order_and_remaining_time(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    get = lambda slug: roadmap_service.get_topic(db_session, slug)  # noqa: E731
    roadmap_service.set_topic_status(db_session, get("peremennye"), TopicStatus.REVIEW)
    roadmap_service.set_topic_status(db_session, get("terminal"), TopicStatus.IN_PROGRESS)
    # На «Терминал» (оценка 2 часа) уже потрачено 50 минут.
    db_session.add(StudySession(topic=get("terminal"), day=MONDAY, minutes=50))
    db_session.commit()

    queue = planner_service.collect_plan_topics(db_session, roadmap_service.get_stages(db_session))

    assert [(item.topic.slug, item.kind, item.remaining_minutes) for item in queue] == [
        ("peremennye", "revise", 30),  # сначала то, что нужно освежить
        ("terminal", "study", 70),  # затем начатое: 120 − 50
        ("usloviya", "study", 120),  # затем новое
    ]


def test_overrun_topic_still_gets_time(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    terminal = roadmap_service.get_topic(db_session, "terminal")
    roadmap_service.set_topic_status(db_session, terminal, TopicStatus.IN_PROGRESS)
    db_session.add(StudySession(topic=terminal, day=MONDAY, minutes=500))  # больше оценки
    db_session.commit()

    queue = planner_service.collect_plan_topics(db_session, roadmap_service.get_stages(db_session))

    assert queue[0].remaining_minutes == planner_service.MIN_REMAINING_MINUTES


def test_done_topics_are_not_planned(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    for slug in ("peremennye", "usloviya", "terminal"):
        topic_ = roadmap_service.get_topic(db_session, slug)
        roadmap_service.set_topic_status(db_session, topic_, TopicStatus.DONE)

    stages = roadmap_service.get_stages(db_session)
    assert planner_service.collect_plan_topics(db_session, stages) == []


# --- Расписание --------------------------------------------------------------------


def test_default_schedule(db_session: Session):
    schedule = schedule_service.get_schedule(db_session)

    assert schedule == {0: 120, 1: 0, 2: 120, 3: 120, 4: 0, 5: 210, 6: 120}
    assert schedule_service.weekly_hours(schedule) == 11.5


def test_schedule_is_saved_and_clamped(db_session: Session):
    schedule_service.save_schedule(db_session, {0: 1.5, 1: -3, 2: 99, 5: 4})

    schedule = schedule_service.get_schedule(db_session)
    assert schedule[0] == 90
    assert schedule[1] == 0  # отрицательное превращается в ноль
    assert schedule[2] == schedule_service.MAX_MINUTES_PER_DAY
    assert schedule[3] == 0  # не указанный день — без занятий
    assert schedule[5] == 240


def test_broken_schedule_falls_back_to_default(db_session: Session):
    from app.models import Setting

    db_session.add(Setting(key=schedule_service.SETTING_KEY, value="это не JSON"))
    db_session.commit()

    assert schedule_service.get_schedule(db_session) == schedule_service.DEFAULT_SCHEDULE
