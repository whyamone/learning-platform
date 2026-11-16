"""Точка входа: здесь создаётся FastAPI-приложение.

Сервер запускается командой:

    uvicorn app.main:app

что означает: «в файле app/main.py возьми переменную app».
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.config import get_settings
from app.db import SessionLocal
from app.routers import health, journal, pages, quiz, review, roadmap, time
from app.services.content_loader import ContentProblem
from app.services.importer import ImportReport, import_content
from app.templating import APP_DIR

# Логгер пишет сообщения в терминал. «uvicorn.error» — стандартный логгер сервера
# (несмотря на название, в него пишут и обычные сообщения, не только ошибки).
logger = logging.getLogger("uvicorn.error")


def run_startup_import() -> ImportReport:
    """Импортировать материалы из content/ в базу при запуске приложения."""
    settings = get_settings()
    try:
        with SessionLocal() as db:
            report = import_content(db, settings.content_dir)
    except SQLAlchemyError as error:
        # Чаще всего это значит, что в базе ещё нет таблиц (не применены миграции).
        # Приложение всё равно запускаем: ошибку будет видно в логах и на странице карты.
        logger.error("Не удалось импортировать материалы: %s", error)
        return ImportReport(
            problems=[
                ContentProblem(
                    "база данных",
                    "Импорт не выполнен. Проверь, что миграции применены: make migrate.",
                )
            ]
        )

    logger.info(
        "Материалы импортированы: этапов %d, модулей %d, тем %d, "
        "вопросов %d, карточек %d, замечаний %d",
        report.stages,
        report.modules,
        report.topics,
        report.questions,
        report.cards,
        len(report.problems),
    )
    return report


def create_app(*, import_on_startup: bool = True) -> FastAPI:
    """Собрать приложение: настройки, статические файлы, маршруты.

    `import_on_startup=False` используют тесты: им не нужно, чтобы
    приложение при запуске читало настоящую папку content/ и настоящую базу.
    """
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Код до yield выполняется один раз при запуске сервера,
        # код после yield — при остановке (нам там делать нечего).
        if import_on_startup:
            app.state.import_report = run_startup_import()
        yield

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
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
    app.include_router(roadmap.router)
    app.include_router(quiz.router)
    app.include_router(review.router)
    app.include_router(time.router)
    app.include_router(journal.router)

    return app


app = create_app()
