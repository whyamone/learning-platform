"""Работа со временем."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    """Текущее время по UTC (всемирное время, без часового пояса).

    В базе всегда храним UTC, а в местное время переводим только при показе.
    Так данные не «съезжают» при смене часового пояса или переводе часов.

    SQLite не умеет хранить часовой пояс, поэтому отбрасываем его (`tzinfo=None`).
    """
    return datetime.now(UTC).replace(tzinfo=None)


def local_today(timezone: str) -> date:
    """Сегодняшняя дата в указанном часовом поясе, например "Europe/Moscow".

    Зачем это нужно: внутри контейнера часы идут по UTC. В 02:00 по Москве
    там ещё вчерашний день — без поправки карточки «на сегодня» появлялись бы
    только под утро.
    """
    return datetime.now(ZoneInfo(timezone)).date()
