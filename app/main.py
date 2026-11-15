"""Точка входа: здесь создаётся FastAPI-приложение.

Сервер запускается командой:

    uvicorn app.main:app

что означает: «в файле app/main.py возьми переменную app».
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.routers import health, pages
from app.templating import APP_DIR


def create_app() -> FastAPI:
    """Собрать приложение: настройки, статические файлы, маршруты."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        # Автодокументация API не нужна: у нас сайт со страницами, а не публичный API.
        docs_url=None,
        redoc_url=None,
    )

    # Статические файлы (CSS, JS) раздаём из папки app/static по адресу /static.
    # Всё лежит в проекте — поэтому сайт работает без интернета.
    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

    # Подключаем группы маршрутов. Новые разделы будут добавляться сюда же.
    app.include_router(health.router)
    app.include_router(pages.router)

    return app


app = create_app()
