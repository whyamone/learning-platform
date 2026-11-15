"""Общие заготовки (фикстуры) для тестов.

Фикстура — функция, которая готовит что-то нужное тесту. Если в параметрах
теста написать имя фикстуры (например, `client`), pytest сам её вызовет.

Главное правило: тесты никогда не трогают настоящую базу data/app.db.
Для каждого теста создаётся своя временная база, которая потом удаляется.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  — чтобы Base узнал обо всех таблицах
from app.db import Base, get_db, make_engine
from app.main import create_app


@pytest.fixture
def db_session(tmp_path) -> Iterator[Session]:
    """Сеанс к пустой временной базе со всеми таблицами."""
    # tmp_path — встроенная фикстура pytest: уникальная временная папка.
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """«Браузер» для тестов: умеет открывать страницы приложения."""
    application = create_app()

    # Подменяем зависимость get_db: приложение будет работать
    # с временной базой вместо настоящей.
    application.dependency_overrides[get_db] = lambda: db_session

    with TestClient(application) as test_client:
        yield test_client
