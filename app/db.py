"""Подключение к базе данных.

Три главных понятия SQLAlchemy:

* engine  — «двигатель»: знает, где лежит база и как с ней говорить;
* session — «сеанс»: через него мы читаем и записываем данные;
* Base    — общий родитель для всех моделей (классов-таблиц).
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Родитель всех моделей. Сам таблицей не является."""


def make_engine(database_url: str) -> Engine:
    """Создать engine для указанного адреса базы.

    Вынесено в функцию, чтобы тесты могли создать отдельную временную базу.
    """
    engine = create_engine(
        database_url,
        # SQLite по умолчанию разрешает работать с соединением только из того
        # потока, где оно создано. FastAPI обрабатывает запросы в разных
        # потоках, поэтому эту проверку отключаем.
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        # В SQLite проверка внешних ключей (связей между таблицами)
        # выключена по умолчанию — включаем её для каждого соединения.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = make_engine(get_settings().database_url)

# Фабрика сеансов: каждый вызов SessionLocal() даёт новый сеанс.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Выдать сеанс базы на время одного запроса и закрыть его после.

    FastAPI вызывает эту функцию сам, когда в маршруте написано
    `db: Session = Depends(get_db)`. Это называется «зависимость».
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
