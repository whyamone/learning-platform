"""Обычные страницы сайта (те, что видит человек в браузере)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.routers.plan import make_plan
from app.services import cards as cards_service
from app.services import dashboard as dashboard_service
from app.services import planner as planner_service
from app.services import roadmap as roadmap_service
from app.services import schedule as schedule_service
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
    # План на неделю берётся из расписания: с ним сравниваются часы и считается прогноз.
    goal_hours = schedule_service.weekly_hours(schedule_service.get_schedule(db))
    pace = dashboard_service.get_pace(db, today, goal_hours)
    plan = make_plan(db, settings)

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "review_count": queue.total,
            "today": today,
            "week": dashboard_service.get_week(db, today, goal_hours),
            "plan_today": planner_service.find_today(plan),
            "plan_next_day": planner_service.find_next_study_day(plan),
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
