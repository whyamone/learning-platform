"""Обычные страницы сайта (те, что видит человек в браузере)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.services import cards as cards_service
from app.services import roadmap as roadmap_service
from app.services.system import database_is_available
from app.templating import templates
from app.timeutils import local_today

router = APIRouter(tags=["страницы"])


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Главная страница: что учить сейчас и прогресс по этапам.

    Позже здесь будет полноценный дашборд с часами и прогнозом.
    """
    stages = roadmap_service.get_stages(db)
    queue = cards_service.get_queue(db, local_today(settings.timezone), settings.new_cards_per_day)

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "review_count": queue.total,
            "next_topic": roadmap_service.get_next_topic(stages),
            "total_progress": roadmap_service.count_progress(
                roadmap_service.get_all_topics(stages)
            ),
            "stage_views": [
                {"stage": stage, "progress": roadmap_service.count_progress(stage.active_topics)}
                for stage in stages
            ],
        },
    )


@router.get("/partials/status", response_class=HTMLResponse)
def status_partial(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Кусочек HTML с состоянием системы.

    Это не целая страница, а фрагмент: HTMX запрашивает его с главной
    страницы и вставляет в нужное место без перезагрузки.
    """
    return templates.TemplateResponse(
        request,
        "partials/status.html",
        {"database_ok": database_is_available(db)},
    )
