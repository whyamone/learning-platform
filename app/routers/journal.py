"""Журнал: заметки и ссылки к темам."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import journal as journal_service
from app.services import roadmap as roadmap_service
from app.templating import templates

router = APIRouter(tags=["журнал"])


@router.get("/journal", response_class=HTMLResponse)
def journal_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Все записи журнала по всем темам."""
    return templates.TemplateResponse(
        request, "journal.html", {"entries": journal_service.list_all(db)}
    )


@router.post("/topics/{slug}/journal", response_class=HTMLResponse)
def add_entry(
    slug: str,
    request: Request,
    text: Annotated[str, Form()] = "",
    url: Annotated[str, Form()] = "",
    db: Session = Depends(get_db),
):
    """Добавить запись к теме (форма на странице темы)."""
    topic = roadmap_service.get_topic(db, slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")

    error = ""
    try:
        journal_service.add_entry(db, topic, text, url)
    except journal_service.JournalError as exc:
        error = str(exc)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request,
            "partials/topic_journal.html",
            # При ошибке возвращаем введённое обратно в поля, чтобы не набирать заново.
            {
                "topic": topic,
                "error": error,
                "text": text if error else "",
                "url": url if error else "",
            },
        )
    return RedirectResponse(
        request.url_for("topic_page", slug=slug), status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/journal/{entry_id}/delete", response_class=HTMLResponse)
def delete_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    """Удалить запись журнала."""
    entry = journal_service.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    topic = entry.topic
    journal_service.delete_entry(db, entry)

    if request.headers.get("HX-Request"):
        db.refresh(topic)
        return templates.TemplateResponse(
            request,
            "partials/topic_journal.html",
            {"topic": topic, "error": "", "text": "", "url": ""},
        )
    return RedirectResponse(request.url_for("journal_page"), status_code=status.HTTP_303_SEE_OTHER)
