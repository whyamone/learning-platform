"""Планировщик: раскладывает темы и повторения по дням.

Главная идея: план нигде не хранится. Он вычисляется заново при каждом
открытии страницы из четырёх вещей:

* расписания (сколько минут в какой день недели);
* списка непройденных тем и оставшегося на них времени;
* уже записанных занятий;
* сегодняшней даты.

Поэтому пропущенное занятие не нужно «отрабатывать» и план не нужно
чинить: завтра он просто построится от нового «сегодня», и темы сдвинутся.

Функция build_plan — чистая: она не обращается к базе. Данные для неё
собирает collect_plan_topics.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Stage, StudySession, Topic, TopicStatus
from app.services.dashboard import WEEKDAY_NAMES, week_start

# Сколько минут в учебный день отводится на карточки.
REVIEW_MINUTES = 10
# Сколько минут уходит на то, чтобы освежить тему с пометкой «Повторить».
REVISE_MINUTES = 30
# Кусочек темы короче этого в день не ставим: за пять минут в тему не войти.
MIN_CHUNK_MINUTES = 15
# Если на тему потрачено больше оценки, а она не закрыта, оставляем ей хотя бы столько.
MIN_REMAINING_MINUTES = 30


@dataclass(frozen=True)
class PlanTopic:
    """Тема в очереди планировщика."""

    topic: Topic
    remaining_minutes: int
    kind: str  # "study" — изучение, "revise" — повторение пройденной темы


@dataclass(frozen=True)
class PlanItem:
    """Один пункт плана на день."""

    kind: str  # "study", "revise" или "cards"
    minutes: int
    topic: Topic | None = None
    # True — тема начата в один из предыдущих дней и здесь продолжается.
    is_continuation: bool = False
    # True — в этот день тема по плану заканчивается.
    is_final: bool = False


@dataclass
class PlanDay:
    day: date
    name: str
    scheduled_minutes: int  # сколько минут стоит в расписании
    studied_minutes: int  # сколько уже записано занятий в этот день
    is_today: bool
    is_past: bool
    items: list[PlanItem] = field(default_factory=list)

    @property
    def planned_minutes(self) -> int:
        return sum(item.minutes for item in self.items)

    @property
    def is_rest(self) -> bool:
        """День без занятий по расписанию."""
        return self.scheduled_minutes == 0


@dataclass
class PlanWeek:
    title: str
    days: list[PlanDay]

    @property
    def scheduled_minutes(self) -> int:
        return sum(day.scheduled_minutes for day in self.days)

    @property
    def studied_minutes(self) -> int:
        return sum(day.studied_minutes for day in self.days)


def build_plan(
    today: date,
    schedule: Mapping[int, int],
    topics: Sequence[PlanTopic],
    studied_by_day: Mapping[date, int],
    include_cards: bool,
    weeks: int = 2,
) -> list[PlanWeek]:
    """Построить план с понедельника текущей недели на `weeks` недель вперёд.

    Прошедшие дни показывают только факт — сколько занимался. Сегодняшний
    день получает то, что осталось от расписания. Будущие дни — полный план.
    """
    # Очередь тем превращаем в изменяемый список [тема, остаток минут, вид, уже начата].
    queue = [[item.topic, item.remaining_minutes, item.kind, False] for item in topics]
    monday = week_start(today)
    result: list[PlanWeek] = []

    for week_number in range(weeks):
        days: list[PlanDay] = []
        for offset in range(7):
            day = monday + timedelta(days=week_number * 7 + offset)
            scheduled = schedule.get(day.weekday(), 0)
            studied = studied_by_day.get(day, 0)
            plan_day = PlanDay(
                day=day,
                name=WEEKDAY_NAMES[day.weekday()],
                scheduled_minutes=scheduled,
                studied_minutes=studied,
                is_today=day == today,
                is_past=day < today,
            )
            days.append(plan_day)

            if plan_day.is_past:
                continue  # прошлое не планируем

            # Сегодня планируем только то, что ещё не сделано.
            capacity = max(0, scheduled - studied) if plan_day.is_today else scheduled
            if capacity <= 0:
                continue

            if include_cards:
                minutes = min(REVIEW_MINUTES, capacity)
                plan_day.items.append(PlanItem(kind="cards", minutes=minutes))
                capacity -= minutes

            _fill_day(plan_day, queue, capacity)

        title = "Эта неделя" if week_number == 0 else "Следующая неделя"
        if week_number > 1:
            title = f"Через {week_number} нед."
        result.append(PlanWeek(title=title, days=days))

    return result


def _fill_day(plan_day: PlanDay, queue: list[list], capacity: int) -> None:
    """Заполнить день темами из очереди, пока есть время."""
    while queue and capacity >= MIN_CHUNK_MINUTES:
        topic, remaining, kind, started = queue[0]
        minutes = min(remaining, capacity)

        # Не оставляем от темы крошечный хвост на следующий день:
        # если не хватает меньше пятнадцати минут, считаем, что тема влезла.
        tail = remaining - minutes
        if 0 < tail < MIN_CHUNK_MINUTES:
            tail = 0

        plan_day.items.append(
            PlanItem(
                kind=kind,
                minutes=minutes,
                topic=topic,
                is_continuation=started,
                is_final=tail == 0,
            )
        )
        capacity -= minutes

        if tail == 0:
            queue.pop(0)
        else:
            queue[0][1] = tail
            queue[0][3] = True


def collect_plan_topics(db: Session, stages: Sequence[Stage]) -> list[PlanTopic]:
    """Собрать очередь тем для планировщика.

    Порядок: сначала темы с пометкой «Повторить», затем начатые,
    затем не начатые — в том порядке, в каком они идут по дорожной карте.
    """
    # Сколько минут уже записано на каждую тему.
    rows = db.execute(
        select(StudySession.topic_id, func.sum(StudySession.minutes))
        .where(StudySession.topic_id.is_not(None))
        .group_by(StudySession.topic_id)
    ).all()
    spent = {topic_id: int(minutes or 0) for topic_id, minutes in rows}

    all_topics = [topic for stage in stages for topic in stage.active_topics]

    def remaining(topic: Topic) -> int:
        estimate = round(topic.estimated_hours * 60)
        return max(MIN_REMAINING_MINUTES, estimate - spent.get(topic.id, 0))

    revise = [
        PlanTopic(topic, REVISE_MINUTES, "revise")
        for topic in all_topics
        if topic.status == TopicStatus.REVIEW
    ]
    in_progress = [
        PlanTopic(topic, remaining(topic), "study")
        for topic in all_topics
        if topic.status == TopicStatus.IN_PROGRESS
    ]
    not_started = [
        PlanTopic(topic, remaining(topic), "study")
        for topic in all_topics
        if topic.status == TopicStatus.NOT_STARTED
    ]
    return [*revise, *in_progress, *not_started]


def get_studied_by_day(db: Session, start: date, end: date) -> dict[date, int]:
    """Минуты занятий по дням за период."""
    rows = db.execute(
        select(StudySession.day, func.sum(StudySession.minutes))
        .where(StudySession.day >= start, StudySession.day <= end)
        .group_by(StudySession.day)
    ).all()
    return {day: int(minutes or 0) for day, minutes in rows}


def find_today(weeks: Sequence[PlanWeek]) -> PlanDay | None:
    for week in weeks:
        for day in week.days:
            if day.is_today:
                return day
    return None


def find_next_study_day(weeks: Sequence[PlanWeek]) -> PlanDay | None:
    """Ближайший будущий день, на который что-то запланировано."""
    for week in weeks:
        for day in week.days:
            if not day.is_past and not day.is_today and day.items:
                return day
    return None
