"""Обычные страницы сайта (те, что видит человек в браузере)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.services import cards as cards_service
from app.services import dashboard as dashboard_service
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
    """Дашборд: неделя, серия дней, что учить сейчас, прогресс и прогноз."""
    today = local_today(settings.timezone)
    stages = roadmap_service.get_stages(db)
    queue = cards_service.get_queue(db, today, settings.new_cards_per_day)
    pace = dashboard_service.get_pace(db, today, settings.weekly_goal_hours)

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "review_count": queue.total,
            "today": today,
            "week": dashboard_service.get_week(db, today, settings.weekly_goal_hours),
            "streak": dashboard_service.calculate_streak(
                dashboard_service.get_active_days(db, settings.timezone), today
            ),
            "pace": pace,
            "forecast": dashboard_service.get_forecast(stages, pace, today),
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
