"""Квиз по теме: страница с вопросами и страница с разбором ответов."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Topic
from app.services import quiz as quiz_service
from app.services import roadmap as roadmap_service
from app.templating import templates

router = APIRouter(tags=["квизы"])


def _get_topic_with_quiz(db: Session, slug: str) -> Topic:
    """Найти тему, у которой есть вопросы. Иначе — «404 не найдено»."""
    topic = roadmap_service.get_topic(db, slug)
    if topic is None or not topic.questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Квиз не найден")
    return topic


@router.get("/topics/{slug}/quiz", response_class=HTMLResponse)
def quiz_page(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Показать вопросы."""
    topic = _get_topic_with_quiz(db, slug)
    return templates.TemplateResponse(request, "quiz.html", {"topic": topic})


@router.post("/topics/{slug}/quiz", response_class=HTMLResponse)
async def submit_quiz(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Проверить ответы, сохранить попытку и показать разбор.

    Это единственный маршрут с `async def`. Причина: число полей формы заранее
    неизвестно (у каждой темы своё количество вопросов), поэтому форму читаем
    целиком через `await request.form()`, а `await` разрешён только в async-функции.
    """
    topic = _get_topic_with_quiz(db, slug)

    form = await request.form()
    answers = quiz_service.parse_answers(form)
    result = quiz_service.grade_quiz(topic.questions, answers)
    quiz_service.save_attempt(db, topic, result)

    return templates.TemplateResponse(
        request,
        "quiz_result.html",
        {"topic": topic, "result": result, "stats": quiz_service.get_stats(db, topic)},
    )
