"""Логика квизов: проверка ответов и история попыток."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import QuizAttempt, QuizQuestion, Topic

# С какого результата квиз считается пройденным.
PASSING_PERCENT = 80


@dataclass(frozen=True)
class QuestionResult:
    """Разбор одного вопроса: что выбрано и верно ли."""

    question: QuizQuestion
    chosen_index: int | None  # None — на вопрос не ответили
    is_correct: bool


@dataclass(frozen=True)
class QuizResult:
    """Итог всей попытки."""

    items: list[QuestionResult]

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def correct(self) -> int:
        return sum(1 for item in self.items if item.is_correct)

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 0
        return round(self.correct * 100 / self.total)

    @property
    def is_passed(self) -> bool:
        return self.percent >= PASSING_PERCENT


@dataclass(frozen=True)
class QuizStats:
    """Сводка по прошлым попыткам — для страницы темы."""

    attempts: int
    best_percent: int | None
    last_percent: int | None


def grade_quiz(questions: Sequence[QuizQuestion], answers: Mapping[int, int]) -> QuizResult:
    """Проверить ответы.

    `answers` — словарь {номер вопроса в базе: номер выбранного варианта}.
    Вопрос, которого в словаре нет, считается оставленным без ответа.
    """
    items = []
    for question in questions:
        chosen_index = answers.get(question.id)
        items.append(
            QuestionResult(
                question=question,
                chosen_index=chosen_index,
                is_correct=chosen_index == question.correct_index,
            )
        )
    return QuizResult(items=items)


def parse_answers(form: Mapping[str, object]) -> dict[int, int]:
    """Достать ответы из данных HTML-формы.

    Поля формы называются «q-<номер вопроса>», значение — номер варианта.
    Всё, что не подходит под этот вид, молча пропускаем: данные из браузера
    нельзя считать надёжными, их всегда нужно проверять.
    """
    answers: dict[int, int] = {}
    for name, value in form.items():
        if not name.startswith("q-"):
            continue
        try:
            answers[int(name.removeprefix("q-"))] = int(str(value))
        except ValueError:
            continue
    return answers


def save_attempt(db: Session, topic: Topic, result: QuizResult) -> QuizAttempt:
    """Записать попытку в историю."""
    attempt = QuizAttempt(topic=topic, correct_count=result.correct, total_count=result.total)
    db.add(attempt)
    db.commit()
    return attempt


def get_stats(db: Session, topic: Topic) -> QuizStats:
    """Сколько было попыток, лучший и последний результат."""
    attempts = list(
        db.scalars(
            select(QuizAttempt)
            .where(QuizAttempt.topic_id == topic.id)
            .order_by(QuizAttempt.created_at, QuizAttempt.id)
        )
    )
    if not attempts:
        return QuizStats(attempts=0, best_percent=None, last_percent=None)
    return QuizStats(
        attempts=len(attempts),
        best_percent=max(attempt.percent for attempt in attempts),
        last_percent=attempts[-1].percent,
    )


def count_questions(db: Session) -> int:
    """Сколько всего вопросов в базе."""
    return db.scalar(select(func.count()).select_from(QuizQuestion)) or 0
