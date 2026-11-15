"""Страницы дорожной карты и отдельной темы."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Topic, TopicStatus
from app.services import quiz as quiz_service
from app.services import roadmap as roadmap_service
from app.services.importer import import_content
from app.templating import templates

router = APIRouter(tags=["дорожная карта"])


def _get_topic_or_404(db: Session, slug: str) -> Topic:
    """Найти тему или ответить «404 — не найдено»."""
    topic = roadmap_service.get_topic(db, slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")
    return topic


@router.get("/roadmap", response_class=HTMLResponse)
def roadmap(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Вся дорожная карта: этапы, модули, темы и прогресс."""
    stages = roadmap_service.get_stages(db)

    # Для каждого этапа заранее считаем прогресс, чтобы шаблон только показывал.
    stage_views = [
        {"stage": stage, "progress": roadmap_service.count_progress(stage.active_topics)}
        for stage in stages
    ]

    return templates.TemplateResponse(
        request,
        "roadmap.html",
        {
            "stage_views": stage_views,
            # Отчёт о последнем импорте хранится в памяти приложения (см. app/main.py).
            "import_report": getattr(request.app.state, "import_report", None),
        },
    )


@router.get("/topics/{slug}", response_class=HTMLResponse)
def topic_page(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Страница одной темы: теория, практика, материалы."""
    topic = _get_topic_or_404(db, slug)
    stages = roadmap_service.get_stages(db)

    return templates.TemplateResponse(
        request,
        "topic.html",
        {
            "topic": topic,
            "neighbors": roadmap_service.get_neighbors(stages, topic),
            "quiz_stats": quiz_service.get_stats(db, topic),
        },
    )


@router.post("/topics/{slug}/status", response_class=HTMLResponse)
def change_topic_status(
    slug: str,
    request: Request,
    # Form(...) — значение приходит из HTML-формы. Тип TopicStatus означает,
    # что FastAPI сам отклонит любое значение не из списка статусов.
    new_status: Annotated[TopicStatus, Form(alias="status")],
    db: Session = Depends(get_db),
):
    """Сменить статус темы (кнопки на странице темы)."""
    topic = _get_topic_or_404(db, slug)
    roadmap_service.set_topic_status(db, topic, new_status)

    # HTMX добавляет к своим запросам заголовок HX-Request. Если он есть —
    # отдаём только обновлённый кусочек страницы. Если нет (JavaScript выключен) —
    # обычная форма: перенаправляем обратно на страницу темы.
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "partials/topic_status.html", {"topic": topic})
    return RedirectResponse(
        request.url_for("topic_page", slug=slug), status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/content/reimport")
def reimport_content(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Перечитать папку content/ без перезапуска приложения."""
    request.app.state.import_report = import_content(db, settings.content_dir)
    # 303 — «смотри другую страницу»: после отправки формы браузер откроет карту.
    return RedirectResponse(request.url_for("roadmap"), status_code=status.HTTP_303_SEE_OTHER)
