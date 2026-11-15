"""Логика дорожной карты: чтение карты, подсчёт прогресса, смена статусов."""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Module, Stage, Topic, TopicProgress, TopicStatus
from app.timeutils import utcnow


@dataclass(frozen=True)
class Progress:
    """Сколько тем пройдено из скольких."""

    done: int
    total: int

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 0
        return round(self.done * 100 / self.total)


@dataclass(frozen=True)
class TopicNeighbors:
    """Соседние темы — для кнопок «назад» и «дальше» на странице темы."""

    previous: Topic | None
    next: Topic | None


def get_stages(db: Session) -> list[Stage]:
    """Вернуть все видимые этапы вместе с модулями, темами и прогрессом.

    `selectinload` просит SQLAlchemy загрузить вложенные данные заранее,
    несколькими запросами. Без него каждое обращение к `stage.modules`
    или `topic.progress` делало бы отдельный запрос в базу.
    """
    query = (
        select(Stage)
        .where(Stage.is_active)
        .order_by(Stage.position)
        .options(
            selectinload(Stage.modules).selectinload(Module.topics).selectinload(Topic.progress)
        )
    )
    return list(db.scalars(query))


def count_progress(topics: Iterable[Topic]) -> Progress:
    """Посчитать прогресс по списку тем."""
    topics = list(topics)
    done = sum(1 for topic in topics if topic.status.is_completed)
    return Progress(done=done, total=len(topics))


def get_all_topics(stages: Iterable[Stage]) -> list[Topic]:
    """Все видимые темы карты одним списком — в том порядке, в котором их проходят."""
    return [topic for stage in stages for topic in stage.active_topics]


def get_topic(db: Session, slug: str) -> Topic | None:
    """Найти видимую тему по её slug. Если такой нет — вернуть None."""
    query = select(Topic).where(Topic.slug == slug, Topic.is_active)
    return db.scalar(query)


def get_neighbors(stages: Iterable[Stage], topic: Topic) -> TopicNeighbors:
    """Найти предыдущую и следующую темы относительно данной."""
    topics = get_all_topics(stages)
    ids = [item.id for item in topics]
    if topic.id not in ids:
        return TopicNeighbors(previous=None, next=None)

    index = ids.index(topic.id)
    previous = topics[index - 1] if index > 0 else None
    following = topics[index + 1] if index + 1 < len(topics) else None
    return TopicNeighbors(previous=previous, next=following)


def get_next_topic(stages: Iterable[Stage]) -> Topic | None:
    """Выбрать тему, которой стоит заняться сейчас.

    Сначала — та, что уже «в процессе». Если таких нет — первая не начатая.
    """
    topics = get_all_topics(stages)
    for wanted in (TopicStatus.IN_PROGRESS, TopicStatus.NOT_STARTED):
        for topic in topics:
            if topic.status == wanted:
                return topic
    return None


def set_topic_status(db: Session, topic: Topic, status: TopicStatus) -> None:
    """Изменить статус темы и проставить даты начала и завершения."""
    progress = topic.progress
    if progress is None:
        progress = TopicProgress()
        topic.progress = progress

    now = utcnow()
    progress.status = status.value

    if status == TopicStatus.NOT_STARTED:
        # Вернули в начало — даты больше не имеют смысла.
        progress.started_at = None
        progress.completed_at = None
    else:
        # Дату начала ставим один раз — при первом уходе из «не начато».
        if progress.started_at is None:
            progress.started_at = now
        if status == TopicStatus.DONE:
            progress.completed_at = now
        elif status == TopicStatus.IN_PROGRESS:
            progress.completed_at = None
        # При «повторить» дату завершения не трогаем: тема уже была пройдена.

    db.commit()
