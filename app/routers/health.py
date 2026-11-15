"""Проверка «жив ли сервис».

Адрес /health опрашивает Docker (см. healthcheck в docker-compose.yml),
а ещё его удобно открыть в браузере, если что-то не работает.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app import __version__
from app.db import get_db
from app.services.system import database_is_available

router = APIRouter(tags=["служебное"])


@router.get("/health")
def health(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    """Вернуть состояние приложения и базы данных в формате JSON."""
    database_ok = database_is_available(db)

    if not database_ok:
        # 503 = «сервис недоступен». По этому коду Docker поймёт, что дело плохо.
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if database_ok else "error",
        "database": "ok" if database_ok else "error",
        "version": __version__,
    }
