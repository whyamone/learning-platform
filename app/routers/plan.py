"""Страница «План»: недельный план и расписание занятий."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
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


def _parse_hours(raw: str) -> float:
    """Превратить текст из поля формы в число часов. Понимает и «1,5», и «1.5»."""
    try:
        return float(raw.replace(",", ".").strip() or 0)
    except ValueError:
        return 0.0  # непонятное значение считаем днём без занятий


@router.post("/plan/schedule")
def save_schedule(
    request: Request,
    # Семь полей формы, по одному на день недели. Значения — в часах.
    day0: Annotated[str, Form()] = "0",
    day1: Annotated[str, Form()] = "0",
    day2: Annotated[str, Form()] = "0",
    day3: Annotated[str, Form()] = "0",
    day4: Annotated[str, Form()] = "0",
    day5: Annotated[str, Form()] = "0",
    day6: Annotated[str, Form()] = "0",
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Сохранить расписание."""
    values = [day0, day1, day2, day3, day4, day5, day6]
    schedule_service.save_schedule(db, {day: _parse_hours(raw) for day, raw in enumerate(values)})
    return RedirectResponse(request.url_for("plan_page"), status_code=status.HTTP_303_SEE_OTHER)
