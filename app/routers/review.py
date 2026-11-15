"""Повторение карточек: очередь «повторить сегодня»."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.services import cards as cards_service
from app.services.sm2 import Grade
from app.templating import templates
from app.timeutils import local_today

router = APIRouter(tags=["повторение"])


def _queue_context(db: Session, settings: Settings) -> dict:
    """Данные для показа очереди — общие для страницы и для её фрагмента."""
    queue = cards_service.get_queue(db, local_today(settings.timezone), settings.new_cards_per_day)
    card = queue.next_card
    return {
        "queue": queue,
        "card": card,
        "intervals": cards_service.preview_intervals(card) if card else {},
        "grades": list(Grade),
    }


@router.get("/review", response_class=HTMLResponse)
def review_page(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Страница повторения: показывает одну карточку из очереди."""
    return templates.TemplateResponse(request, "review.html", _queue_context(db, settings))


@router.post("/review/{card_id}", response_class=HTMLResponse)
def grade_card(
    card_id: int,
    request: Request,
    grade: Annotated[Grade, Form()],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Принять оценку ответа и показать следующую карточку."""
    card = cards_service.get_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Карточка не найдена")

    cards_service.grade_card(db, card, grade, local_today(settings.timezone))

    # Как и с кнопками статуса: HTMX получает кусочек страницы,
    # обычная форма — перенаправление на страницу повторения.
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request, "partials/review_card.html", _queue_context(db, settings)
        )
    return RedirectResponse(request.url_for("review_page"), status_code=status.HTTP_303_SEE_OTHER)
