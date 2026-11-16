"""Расчёты для дашборда: часы за неделю, серия дней, темп и прогноз.

Функции разделены на два вида. «Чистые» (calculate_streak, forecast_dates,
week_start) получают готовые данные и ничего не знают о базе — их легко
проверять. Остальные достают данные из базы и передают чистым.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CardReview, Stage, StudySession

WEEKDAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
# За сколько последних дней считается темп.
PACE_WINDOW_DAYS = 28
# Если за это окно записано меньше часа, своего темпа ещё нет.
MIN_MINUTES_FOR_PACE = 60
# Свой темп считаем только после двух недель занятий. Иначе одно занятие
# в первый день дало бы «темп 2 часа в неделю» и прогноз на годы вперёд.
MIN_DAYS_FOR_PACE = 14


@dataclass(frozen=True)
class DayStat:
    """Один день недели на графике."""

    day: date
    name: str
    minutes: int
    is_today: bool
    is_future: bool
    # Высота столбца в процентах от самого высокого за неделю.
    height_percent: int


@dataclass(frozen=True)
class WeekStat:
    days: list[DayStat]
    total_minutes: int
    goal_minutes: int

    @property
    def goal_percent(self) -> int:
        if self.goal_minutes == 0:
            return 0
        return min(100, round(self.total_minutes * 100 / self.goal_minutes))


@dataclass(frozen=True)
class Streak:
    current: int  # сколько дней подряд ты занимаешься сейчас
    best: int  # самая длинная серия за всё время
    studied_today: bool


@dataclass(frozen=True)
class Pace:
    hours_per_week: float
    # True — темп посчитан по твоим занятиям. False — занятий ещё мало,
    # вместо темпа взят план на неделю.
    is_measured: bool


@dataclass(frozen=True)
class StageForecast:
    stage: Stage
    remaining_hours: float
    finish_date: date | None  # None — этап уже закрыт


# --- Неделя ---------------------------------------------------------------------


def week_start(day: date) -> date:
    """Понедельник той недели, в которую попадает день."""
    return day - timedelta(days=day.weekday())


def get_week(db: Session, today: date, goal_hours: float) -> WeekStat:
    """Минуты занятий по дням текущей недели."""
    monday = week_start(today)
    sunday = monday + timedelta(days=6)

    rows = db.execute(
        select(StudySession.day, func.sum(StudySession.minutes))
        .where(StudySession.day >= monday, StudySession.day <= sunday)
        .group_by(StudySession.day)
    ).all()
    minutes_by_day = {day: int(minutes or 0) for day, minutes in rows}

    # Высоту столбцов считаем от самого большого дня, но не меньше двух часов:
    # иначе единственное десятиминутное занятие заняло бы весь график.
    scale = max([120, *minutes_by_day.values()])

    days = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        minutes = minutes_by_day.get(day, 0)
        days.append(
            DayStat(
                day=day,
                name=WEEKDAY_NAMES[offset],
                minutes=minutes,
                is_today=day == today,
                is_future=day > today,
                height_percent=round(minutes * 100 / scale),
            )
        )

    return WeekStat(
        days=days,
        total_minutes=sum(minutes_by_day.values()),
        goal_minutes=round(goal_hours * 60),
    )


# --- Серия дней -----------------------------------------------------------------


def calculate_streak(active_days: Iterable[date], today: date) -> Streak:
    """Посчитать серию дней подряд.

    Серия не обрывается, пока день не закончился: если вчера ты занимался,
    а сегодня ещё нет, текущая серия считается по вчерашний день.
    """
    days = set(active_days)
    studied_today = today in days

    current = 0
    cursor = today if studied_today else today - timedelta(days=1)
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)

    best = 0
    run = 0
    previous: date | None = None
    for day in sorted(days):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day

    return Streak(current=current, best=best, studied_today=studied_today)


def get_active_days(db: Session, timezone: str) -> set[date]:
    """Дни, когда была учёба: занятие с ненулевым временем или повторение карточек."""
    days = set(db.scalars(select(StudySession.day).where(StudySession.minutes > 0).distinct()))

    # Время ответа на карточку хранится в UTC — переводим в местную дату.
    zone = ZoneInfo(timezone)
    for reviewed_at in db.scalars(select(CardReview.reviewed_at)):
        days.add(reviewed_at.replace(tzinfo=UTC).astimezone(zone).date())
    return days


# --- Темп и прогноз -------------------------------------------------------------


def get_pace(db: Session, today: date, goal_hours: float) -> Pace:
    """Средний темп за последние четыре недели, в часах в неделю."""
    window_start = today - timedelta(days=PACE_WINDOW_DAYS - 1)
    minutes = (
        db.scalar(
            select(func.sum(StudySession.minutes)).where(
                StudySession.day >= window_start, StudySession.day <= today
            )
        )
        or 0
    )
    if minutes < MIN_MINUTES_FOR_PACE:
        return Pace(hours_per_week=goal_hours, is_measured=False)

    first_day = db.scalar(select(func.min(StudySession.day)).where(StudySession.minutes > 0))
    days_since_start = (today - first_day).days + 1
    if days_since_start < MIN_DAYS_FOR_PACE:
        return Pace(hours_per_week=goal_hours, is_measured=False)

    # Если ты занимаешься меньше четырёх недель, делим на прошедшее время,
    # а не на четыре, — иначе темп получился бы заниженным.
    weeks = min(days_since_start, PACE_WINDOW_DAYS) / 7
    return Pace(hours_per_week=minutes / 60 / weeks, is_measured=True)


def forecast_dates(
    remaining_hours: Sequence[float], hours_per_week: float, today: date
) -> list[date | None]:
    """Спрогнозировать дату завершения каждого этапа.

    `remaining_hours` — сколько часов осталось в каждом этапе, по порядку.
    Этапы идут друг за другом, поэтому часы накапливаются: чтобы закончить
    второй этап, нужно сначала закончить первый.
    """
    dates: list[date | None] = []
    accumulated = 0.0
    for hours in remaining_hours:
        accumulated += hours
        if hours <= 0 and accumulated <= 0:
            dates.append(None)  # всё уже пройдено
        elif hours_per_week <= 0:
            dates.append(None)
        else:
            dates.append(today + timedelta(days=round(accumulated / hours_per_week * 7)))
    return dates


def get_forecast(stages: Sequence[Stage], pace: Pace, today: date) -> list[StageForecast]:
    """Прогноз по этапам дорожной карты."""
    remaining = [
        sum(t.estimated_hours for t in stage.active_topics if not t.status.is_completed)
        for stage in stages
    ]
    dates = forecast_dates(remaining, pace.hours_per_week, today)
    return [
        StageForecast(
            stage=stage, remaining_hours=hours, finish_date=None if hours <= 0 else finish
        )
        for stage, hours, finish in zip(stages, remaining, dates, strict=True)
    ]
