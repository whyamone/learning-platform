"""Тесты служебного адреса /health."""

from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from app import __version__
from app.db import get_db


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "version": __version__}


def test_health_reports_database_failure(client):
    # Имитируем «сломанную» базу: любой запрос к ней вызывает ошибку.
    broken_db = MagicMock()
    broken_db.execute.side_effect = OperationalError("SELECT 1", {}, Exception("нет базы"))
    client.app.dependency_overrides[get_db] = lambda: broken_db

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["database"] == "error"
