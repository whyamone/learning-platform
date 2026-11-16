"""Общий объект для работы с HTML-шаблонами.

Лежит в отдельном файле, чтобы любой маршрут мог написать
`from app.templating import templates` и не создавать его заново.
"""

from datetime import date
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app import __version__
from app.config import get_settings
from app.models import TopicStatus
from app.services.markdown import render_markdown

APP_DIR = Path(__file__).resolve().parent


def format_hours(hours: float) -> str:
    """Показать часы по-человечески: 2.0 → «2 ч», 2.5 → «2,5 ч»."""
    text = f"{hours:g}".replace(".", ",")
    return f"{text} ч"


MONTHS_GENITIVE = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]  # fmt: skip


def format_duration(minutes: int) -> str:
    """Показать минуты по-человечески: 135 → «2 ч 15 мин», 40 → «40 мин»."""
    hours, rest = divmod(int(minutes), 60)
    if hours and rest:
        return f"{hours} ч {rest} мин"
    if hours:
        return f"{hours} ч"
    return f"{rest} мин"


def format_date(value: date, with_year: bool = False) -> str:
    """Показать дату по-русски: «16 ноября» или «16 ноября 2026»."""
    text = f"{value.day} {MONTHS_GENITIVE[value.month - 1]}"
    return f"{text} {value.year}" if with_year else text


def plural(number: int, one: str, few: str, many: str) -> str:
    """Выбрать форму слова по числу: 1 день, 2 дня, 5 дней, 21 день."""
    tail = abs(number) % 100
    if 11 <= tail <= 14:
        return many
    last = tail % 10
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


templates = Jinja2Templates(directory=APP_DIR / "templates")

# «Глобальные» переменные: доступны в каждом шаблоне без явной передачи.
templates.env.globals["app_name"] = get_settings().app_name
templates.env.globals["app_version"] = __version__
templates.env.globals["all_statuses"] = list(TopicStatus)

# Фильтры: функции, которые в шаблоне вызываются через «|».
# Пример: {{ topic.theory_md | markdown }}
templates.env.filters["markdown"] = render_markdown
templates.env.filters["hours"] = format_hours
templates.env.filters["duration"] = format_duration
templates.env.filters["date_ru"] = format_date
templates.env.filters["plural"] = plural
