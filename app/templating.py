"""Общий объект для работы с HTML-шаблонами.

Лежит в отдельном файле, чтобы любой маршрут мог написать
`from app.templating import templates` и не создавать его заново.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app import __version__
from app.config import get_settings

APP_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=APP_DIR / "templates")

# «Глобальные» переменные: доступны в каждом шаблоне без явной передачи.
templates.env.globals["app_name"] = get_settings().app_name
templates.env.globals["app_version"] = __version__
