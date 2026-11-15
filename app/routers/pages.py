"""Обычные страницы сайта (те, что видит человек в браузере)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.system import database_is_available
from app.templating import templates

router = APIRouter(tags=["страницы"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    """Главная страница. Позже здесь будет дашборд с прогрессом."""
    return templates.TemplateResponse(request, "home.html")


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
