"""Учёт времени: таймер в шапке сайта и страница «Время»."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import StudySession
from app.services import roadmap as roadmap_service
from app.services import study as study_service
from app.templating import templates
from app.timeutils import local_today, utcnow

router = APIRouter(tags=["время"])


def _timer_context(db: Session) -> dict:
    """Данные для показа таймера: идёт ли занятие и сколько минут прошло."""
    running = study_service.get_running(db)
    return {
        "running": running,
        "elapsed": study_service.elapsed_minutes(running, utcnow()) if running else 0,
    }


def _get_session_or_404(db: Session, session_id: int) -> StudySession:
    session = study_service.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Занятие не найдено")
    return session


def _time_page(request: Request, db: Session, settings: Settings, error: str = "") -> HTMLResponse:
    """Собрать страницу «Время». При ошибке в форме показываем её здесь же."""
    stages = roadmap_service.get_stages(db)
    return templates.TemplateResponse(
        request,
        "time.html",
        {
            "sessions": study_service.list_recent(db),
            "topics": roadmap_service.get_all_topics(stages),
            "today": local_today(settings.timezone),
            "error": error,
            **_timer_context(db),
        },
        status_code=status.HTTP_400_BAD_REQUEST if error else status.HTTP_200_OK,
    )


@router.get("/partials/timer", response_class=HTMLResponse)
def timer_partial(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Кусочек шапки с таймером. HTMX обновляет его раз в минуту."""
    return templates.TemplateResponse(request, "partials/timer.html", _timer_context(db))


@router.post("/timer/start")
def start_timer(
    request: Request,
    topic_slug: Annotated[str, Form()] = "",
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Начать занятие. Если указана тема, время запишется на неё."""
    topic = roadmap_service.get_topic(db, topic_slug) if topic_slug else None
    study_service.start_timer(db, topic, utcnow(), local_today(settings.timezone))

    target = (
        request.url_for("topic_page", slug=topic.slug) if topic else request.url_for("time_page")
    )
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/timer/stop", response_class=HTMLResponse)
def stop_timer(request: Request, db: Session = Depends(get_db)):
    """Закончить занятие."""
    study_service.stop_timer(db, utcnow())

    if request.headers.get("HX-Request"):
        # HX-Refresh просит HTMX перезагрузить страницу целиком: после остановки
        # таймера меняются и шапка, и кнопки, и список занятий.
        return HTMLResponse("", headers={"HX-Refresh": "true"})
    return RedirectResponse(request.url_for("time_page"), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/time", response_class=HTMLResponse)
def time_page(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Страница «Время»: список занятий и ручное добавление."""
    return _time_page(request, db, settings)


@router.post("/time", response_class=HTMLResponse)
def add_session(
    request: Request,
    day: Annotated[date, Form()],
    minutes: Annotated[int, Form()],
    topic_slug: Annotated[str, Form()] = "",
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Добавить занятие вручную."""
    topic = roadmap_service.get_topic(db, topic_slug) if topic_slug else None
    try:
        study_service.add_manual(db, day, minutes, topic, local_today(settings.timezone))
    except study_service.StudyError as error:
        return _time_page(request, db, settings, error=str(error))
    return RedirectResponse(request.url_for("time_page"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/time/{session_id}", response_class=HTMLResponse)
def update_session(
    session_id: int,
    request: Request,
    minutes: Annotated[int, Form()],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Исправить длительность занятия."""
    session = _get_session_or_404(db, session_id)
    try:
        study_service.update_minutes(db, session, minutes)
    except study_service.StudyError as error:
        return _time_page(request, db, settings, error=str(error))
    return RedirectResponse(request.url_for("time_page"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/time/{session_id}/delete")
def delete_session(
    session_id: int, request: Request, db: Session = Depends(get_db)
) -> RedirectResponse:
    """Удалить занятие."""
    study_service.delete_session(db, _get_session_or_404(db, session_id))
    return RedirectResponse(request.url_for("time_page"), status_code=status.HTTP_303_SEE_OTHER)
