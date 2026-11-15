"""Очередь повторения карточек.

Здесь алгоритм SM-2 (см. sm2.py) соединяется с базой данных:
какие карточки показать сегодня и что записать после ответа.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Card, CardReview, CardState, Module, Stage, Topic, TopicProgress, TopicStatus
from app.services.sm2 import Grade, Schedule, next_schedule
from app.timeutils import utcnow


@dataclass(frozen=True)
class ReviewQueue:
    """Что повторять сегодня."""

    due: list[Card]  # карточки, срок повторения которых подошёл
    new: list[Card]  # новые карточки из начатых тем (с учётом дневного лимита)

    @property
    def total(self) -> int:
        return len(self.due) + len(self.new)

    @property
    def next_card(self) -> Card | None:
        """Какую карточку показать следующей: сначала долги, потом новые."""
        if self.due:
            return self.due[0]
        if self.new:
            return self.new[0]
        return None


def _visible_cards():
    """Основа запроса: активные карточки тем, которые ты уже начал изучать.

    Карточки не начатых тем не показываем — нет смысла повторять то,
    чего ещё не проходил.
    """
    return (
        select(Card)
        .join(Card.topic)
        .join(Topic.module)
        .join(Module.stage)
        .join(Topic.progress)
        .where(
            Card.is_active,
            Topic.is_active,
            TopicProgress.status != TopicStatus.NOT_STARTED.value,
        )
        .options(selectinload(Card.topic), selectinload(Card.state))
    )


def get_queue(db: Session, today: date, new_cards_per_day: int) -> ReviewQueue:
    """Собрать очередь на сегодня."""
    # 1. Долги: карточки с расписанием, у которых день показа уже наступил.
    #    Первыми идут самые просроченные.
    due_query = (
        _visible_cards()
        .join(Card.state)
        .where(CardState.due_date <= today)
        .order_by(CardState.due_date, Card.id)
    )
    due = list(db.scalars(due_query))

    # 2. Новые: карточки без расписания. Их выдаём понемногу в день.
    introduced_today = (
        db.scalar(
            select(func.count()).select_from(CardState).where(CardState.introduced_on == today)
        )
        or 0
    )
    new_limit = max(0, new_cards_per_day - introduced_today)

    new: list[Card] = []
    if new_limit > 0:
        new_query = (
            _visible_cards()
            # outerjoin — «левое соединение»: карточки остаются в выборке,
            # даже если расписания у них нет. Именно такие нам и нужны.
            .outerjoin(Card.state)
            .where(CardState.card_id.is_(None))
            # В том порядке, в котором темы идут по дорожной карте.
            .order_by(Stage.position, Module.position, Topic.position, Card.position)
            .limit(new_limit)
        )
        new = list(db.scalars(new_query))

    return ReviewQueue(due=due, new=new)


def get_card(db: Session, card_id: int) -> Card | None:
    """Найти активную карточку по номеру."""
    return db.scalar(select(Card).where(Card.id == card_id, Card.is_active))


def grade_card(db: Session, card: Card, grade: Grade, today: date) -> CardState:
    """Записать ответ на карточку и назначить день следующего показа."""
    state = card.state
    current = (
        Schedule()  # новая карточка: расписание по умолчанию
        if state is None
        else Schedule(state.repetitions, state.interval_days, state.ease_factor)
    )
    updated = next_schedule(current, grade.quality)

    if state is None:
        state = CardState(introduced_on=today, due_date=today)
        card.state = state

    state.repetitions = updated.repetitions
    state.interval_days = updated.interval_days
    state.ease_factor = updated.ease_factor
    state.due_date = today + timedelta(days=updated.interval_days)
    state.last_reviewed_at = utcnow()

    db.add(CardReview(card=card, quality=grade.quality, interval_days=updated.interval_days))
    db.commit()
    return state


def describe_interval(days: int) -> str:
    """Сказать по-человечески, когда карточка вернётся."""
    if days <= 1:
        return "завтра"
    if days < 30:
        return f"через {days} дн."
    if days < 365:
        return f"через {round(days / 30)} мес."
    return f"через {days / 365:.1f} г.".replace(".", ",", 1)


def preview_intervals(card: Card) -> dict[Grade, str]:
    """Для каждой кнопки подсказать, когда карточка вернётся, если её нажать."""
    state = card.state
    current = (
        Schedule()
        if state is None
        else Schedule(state.repetitions, state.interval_days, state.ease_factor)
    )
    return {
        grade: describe_interval(next_schedule(current, grade.quality).interval_days)
        for grade in Grade
    }
