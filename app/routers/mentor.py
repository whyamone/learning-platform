"""ИИ-наставник: чат на странице темы.

Все маршруты работают, только если в настройках включён флаг AI_MENTOR_ENABLED.
Иначе они отвечают «404 не найдено», как будто их нет.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Topic
from app.services import mentor as mentor_service
from app.services import roadmap as roadmap_service
from app.services.mentor import MentorError, MentorMode
from app.templating import templates

router = APIRouter(tags=["наставник"])


def require_mentor(settings: Settings = Depends(get_settings)) -> Settings:
    """Зависимость-«охранник»: пропускает дальше, только если наставник включён."""
    if not settings.ai_mentor_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Наставник выключен")
    return settings


def _get_topic_or_404(db: Session, slug: str) -> Topic:
    topic = roadmap_service.get_topic(db, slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")
    return topic


def mentor_context(
    db: Session,
    settings: Settings,
    topic: Topic,
    mode: MentorMode,
    error: str = "",
    draft: str = "",
) -> dict:
    """Данные для блока наставника. Используется и на странице темы."""
    return {
        "topic": topic,
        "mentor_mode": mode,
        "mentor_modes": list(MentorMode),
        "mentor_history": mentor_service.get_history(db, topic, mode),
        "mentor_error": error,
        "mentor_draft": draft,
        "mentor_model": settings.ollama_model,
    }


@router.get("/topics/{slug}/mentor", response_class=HTMLResponse)
def mentor_block(
    slug: str,
    request: Request,
    mode: MentorMode = MentorMode.EXPLAIN,
    db: Session = Depends(get_db),
    settings: Settings = Depends(require_mentor),
) -> HTMLResponse:
    """Показать разговор в выбранном режиме (переключение вкладок)."""
    topic = _get_topic_or_404(db, slug)
    return templates.TemplateResponse(
        request, "partials/mentor.html", mentor_context(db, settings, topic, mode)
    )


@router.post("/topics/{slug}/mentor", response_class=HTMLResponse)
def ask_mentor(
    slug: str,
    request: Request,
    mode: Annotated[MentorMode, Form()],
    text: Annotated[str, Form()] = "",
    db: Session = Depends(get_db),
    settings: Settings = Depends(require_mentor),
):
    """Отправить сообщение модели и показать ответ."""
    topic = _get_topic_or_404(db, slug)
    error = ""
    draft = ""

    try:
        user_text = mentor_service.validate_user_text(text)
        history = mentor_service.get_history(db, topic, mode)
        messages = mentor_service.build_messages(topic, mode, history, user_text)
        reply = mentor_service.ask_model(
            settings.ollama_base_url,
            settings.ollama_model,
            messages,
            settings.ollama_timeout_seconds,
        )
        mentor_service.save_exchange(db, topic, mode, user_text, reply)
    except MentorError as exc:
        # Ответа нет — показываем причину и возвращаем текст в поле ввода,
        # чтобы его не пришлось набирать заново.
        error = str(exc)
        draft = text

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request,
            "partials/mentor.html",
            mentor_context(db, settings, topic, mode, error=error, draft=draft),
        )
    return RedirectResponse(
        str(request.url_for("topic_page", slug=slug)) + "#mentor",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/topics/{slug}/mentor/clear", response_class=HTMLResponse)
def clear_mentor(
    slug: str,
    request: Request,
    mode: Annotated[MentorMode, Form()],
    db: Session = Depends(get_db),
    settings: Settings = Depends(require_mentor),
):
    """Очистить разговор в выбранном режиме."""
    topic = _get_topic_or_404(db, slug)
    mentor_service.clear_history(db, topic, mode)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request, "partials/mentor.html", mentor_context(db, settings, topic, mode)
        )
    return RedirectResponse(
        str(request.url_for("topic_page", slug=slug)) + "#mentor",
        status_code=status.HTTP_303_SEE_OTHER,
    )
