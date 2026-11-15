"""Таблицы дорожной карты: этап → модуль → тема → ссылки.

Эти таблицы заполняются из файлов папки content/ при импорте.
Править их вручную не нужно: изменения делаются в файлах.

Что означает `is_active`: если файл темы удалить, тема не стирается из базы
(вместе с ней пропал бы твой прогресс), а просто помечается неактивной и
скрывается. Вернёшь файл — тема вернётся вместе с прогрессом.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.progress import TopicStatus

if TYPE_CHECKING:
    # Импорт только для подсказок типов — чтобы файлы не импортировали друг друга по кругу.
    from app.models.card import Card
    from app.models.progress import TopicProgress
    from app.models.quiz import QuizAttempt, QuizQuestion


class Stage(Base):
    """Этап дорожной карты, например «Фундамент» (месяцы 1–4)."""

    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    # slug — короткое имя латиницей из названия папки: «01-fundament» → «fundament».
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    # Порядковый номер из названия папки: «01-fundament» → 1.
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    month_from: Mapped[int] = mapped_column(default=1)
    month_to: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Связь «один этап — много модулей». Модули сразу отсортированы по номеру.
    modules: Mapped[list[Module]] = relationship(
        back_populates="stage", order_by="Module.position", cascade="all, delete-orphan"
    )

    @property
    def active_modules(self) -> list[Module]:
        return [module for module in self.modules if module.is_active]

    @property
    def active_topics(self) -> list[Topic]:
        """Все видимые темы этапа одним списком, по порядку."""
        return [topic for module in self.active_modules for topic in module.active_topics]


class Module(Base):
    """Модуль внутри этапа, например «Python: основы»."""

    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    # ForeignKey — «внешний ключ»: номер этапа, которому принадлежит модуль.
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(default=True)

    stage: Mapped[Stage] = relationship(back_populates="modules")
    topics: Mapped[list[Topic]] = relationship(
        back_populates="module", order_by="Topic.position", cascade="all, delete-orphan"
    )

    @property
    def active_topics(self) -> list[Topic]:
        return [topic for topic in self.topics if topic.is_active]


class Topic(Base):
    """Тема — одна учебная единица: теория, практика и критерий «готово»."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True)
    # slug темы уникален во всей карте: по нему строится адрес /topics/<slug>.
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    estimated_hours: Mapped[float] = mapped_column(default=2.0)

    # Списки храним в формате JSON прямо в ячейке таблицы: отдельные таблицы
    # ради трёх-пяти коротких строк были бы лишним усложнением.
    concepts: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Словарик: [{"term": "variable", "meaning": "переменная"}, ...]
    glossary: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    done_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Тексты в формате Markdown — в HTML они превращаются при показе страницы.
    theory_md: Mapped[str] = mapped_column(Text, default="")
    practice_md: Mapped[str] = mapped_column(Text, default="")

    # Заготовка: тема описана кратко, подробная теория ещё не написана.
    is_stub: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    # Из какого файла тема импортирована (чтобы знать, что править).
    source_path: Mapped[str] = mapped_column(String(300), default="")

    module: Mapped[Module] = relationship(back_populates="topics")
    links: Mapped[list[TopicLink]] = relationship(
        back_populates="topic", order_by="TopicLink.position", cascade="all, delete-orphan"
    )
    # Связь «один к одному»: у темы не больше одной записи о прогрессе.
    progress: Mapped[TopicProgress | None] = relationship(
        back_populates="topic", cascade="all, delete-orphan", uselist=False
    )

    # Вопросы квиза и карточки для повторения (файлы .quiz.yaml и .cards.yaml).
    questions: Mapped[list[QuizQuestion]] = relationship(
        back_populates="topic", order_by="QuizQuestion.position", cascade="all, delete-orphan"
    )
    quiz_attempts: Mapped[list[QuizAttempt]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    cards: Mapped[list[Card]] = relationship(
        back_populates="topic", order_by="Card.position", cascade="all, delete-orphan"
    )

    @property
    def active_cards(self) -> list[Card]:
        return [card for card in self.cards if card.is_active]

    @property
    def status(self) -> TopicStatus:
        """Текущий статус. Пока записи о прогрессе нет — «не начато»."""
        if self.progress is None:
            return TopicStatus.NOT_STARTED
        return TopicStatus(self.progress.status)


class TopicLink(Base):
    """Ссылка на материал к теме: документация, статья, курс, видео."""

    __tablename__ = "topic_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500))
    # Тип материала: docs, article, course, video, book, practice.
    kind: Mapped[str] = mapped_column(String(20), default="article")
    # Язык материала: ru или en.
    lang: Mapped[str] = mapped_column(String(5), default="ru")

    topic: Mapped[Topic] = relationship(back_populates="links")
