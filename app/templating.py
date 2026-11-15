"""Общий объект для работы с HTML-шаблонами.

Лежит в отдельном файле, чтобы любой маршрут мог написать
`from app.templating import templates` и не создавать его заново.
"""

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


templates = Jinja2Templates(directory=APP_DIR / "templates")

# «Глобальные» переменные: доступны в каждом шаблоне без явной передачи.
templates.env.globals["app_name"] = get_settings().app_name
templates.env.globals["app_version"] = __version__
templates.env.globals["all_statuses"] = list(TopicStatus)

# Фильтры: функции, которые в шаблоне вызываются через «|».
# Пример: {{ topic.theory_md | markdown }}
templates.env.filters["markdown"] = render_markdown
templates.env.filters["hours"] = format_hours
