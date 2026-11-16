"""Страница «План»: недельный план и расписание занятий."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.services import planner as planner_service
from app.services import roadmap as roadmap_service
from app.services import schedule as schedule_service
from app.services.dashboard import WEEKDAY_NAMES, week_start
from app.services.planner import PlanWeek
from app.templating import templates
from app.timeutils import local_today

router = APIRouter(tags=["план"])

PLAN_WEEKS = 2


def make_plan(db: Session, settings: Settings) -> list[PlanWeek]:
    """Собрать данные из базы и построить план. Используется здесь и на дашборде."""
    today = local_today(settings.timezone)
    stages = roadmap_service.get_stages(db)
    topics = planner_service.collect_plan_topics(db, stages)
    monday = week_start(today)

    return planner_service.build_plan(
        today=today,
        schedule=schedule_service.get_schedule(db),
        topics=topics,
        studied_by_day=planner_service.get_studied_by_day(db, monday, today),
        # Карточки ставим в план, если хоть одна тема уже начата или пройдена.
        include_cards=any(
            topic.status.value != "not_started" and topic.active_cards
            for stage in stages
            for topic in stage.active_topics
        ),
        weeks=PLAN_WEEKS,
    )


@router.get("/plan", response_class=HTMLResponse)
def plan_page(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    schedule = schedule_service.get_schedule(db)
    return templates.TemplateResponse(
        request,
        "plan.html",
        {
            "weeks": make_plan(db, settings),
            "schedule": schedule,
            "weekday_names": WEEKDAY_NAMES,
            "weekly_hours": schedule_service.weekly_hours(schedule),
        },
    )


@router.post("/plan/schedule")
async def save_schedule(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """Сохранить расписание. Поля формы называются day0 … day6, значения — в часах."""
    form = await request.form()

    hours_by_day: dict[int, float] = {}
    for day in range(7):
        raw = str(form.get(f"day{day}", "0")).replace(",", ".").strip()
        try:
            hours_by_day[day] = float(raw or 0)
        except ValueError:
            hours_by_day[day] = 0  # непонятное значение считаем днём без занятий

    schedule_service.save_schedule(db, hours_by_day)
    return RedirectResponse(request.url_for("plan_page"), status_code=status.HTTP_303_SEE_OTHER)
