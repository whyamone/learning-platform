"""Общие заготовки (фикстуры) для тестов.

Фикстура — функция, которая готовит что-то нужное тесту. Если в параметрах
теста написать имя фикстуры (например, `client`), pytest сам её вызовет.

Главное правило: тесты никогда не трогают настоящую базу data/app.db
и настоящую папку content/. Для каждого теста создаются временные.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  — чтобы Base узнал обо всех таблицах
from app.config import Settings, get_settings
from app.db import Base, get_db, make_engine
from app.main import create_app
from app.services.importer import import_content
from tests.helpers import PYTHON_CARDS, PYTHON_QUIZ, PYTHON_TOPIC, SIMPLE_TOPIC, write_file


@pytest.fixture
def content_dir(tmp_path: Path) -> Path:
    """Временная папка с учебными материалами."""
    root = tmp_path / "content"
    stage = root / "01-fundament"
    write_file(stage / "stage.yaml", "title: Фундамент\nmonth_from: 1\nmonth_to: 4\n")

    write_file(stage / "01-python" / "module.yaml", "title: Python\n")
    write_file(stage / "01-python" / "01-peremennye.md", PYTHON_TOPIC)
    write_file(stage / "01-python" / "01-peremennye.quiz.yaml", PYTHON_QUIZ)
    write_file(stage / "01-python" / "01-peremennye.cards.yaml", PYTHON_CARDS)
    write_file(stage / "01-python" / "02-usloviya.md", SIMPLE_TOPIC.format(title="Условия"))

    write_file(stage / "02-linux" / "module.yaml", "title: Linux\n")
    write_file(stage / "02-linux" / "01-terminal.md", SIMPLE_TOPIC.format(title="Терминал"))
    return root


@pytest.fixture
def db_session(tmp_path: Path) -> Iterator[Session]:
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
def client(db_session: Session, content_dir: Path) -> Iterator[TestClient]:
    """«Браузер» для тестов: умеет открывать страницы приложения.

    База уже наполнена материалами из временной папки content_dir.
    """
    import_content(db_session, content_dir)

    application = create_app(import_on_startup=False)

    # Подменяем зависимости: приложение будет работать с временной базой
    # и временной папкой материалов вместо настоящих.
    application.dependency_overrides[get_db] = lambda: db_session
    application.dependency_overrides[get_settings] = lambda: Settings(content_dir=content_dir)

    with TestClient(application) as test_client:
        yield test_client
