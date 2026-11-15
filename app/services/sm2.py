"""Алгоритм интервального повторения SM-2.

Идея интервального повторения: показывать карточку тогда, когда ты вот-вот
её забудешь. Вспомнил легко — следующий показ нескоро. Не вспомнил — завтра.

SM-2 придуман Петром Возняком для программы SuperMemo в конце 1980-х
и до сих пор лежит в основе Anki и подобных программ.

У каждой карточки три числа:

* repetitions   — сколько раз подряд она вспомнилась;
* interval_days — через сколько дней показать снова;
* ease_factor   — «лёгкость»: на что умножается интервал при успехе.

В этом файле только расчёт — без базы данных и без веба. Такие функции
называют «чистыми»: результат зависит только от входных данных,
поэтому их очень легко проверять тестами.
"""

from dataclasses import dataclass
from enum import StrEnum

DEFAULT_EASE_FACTOR = 2.5
# Ниже этого значения «лёгкость» не опускается: иначе трудные карточки
# показывались бы слишком часто и превращались в наказание.
MIN_EASE_FACTOR = 1.3
# Оценка, начиная с которой ответ считается успешным.
PASSING_QUALITY = 3


class Grade(StrEnum):
    """Четыре кнопки под карточкой.

    В оригинальном SM-2 шкала из шести оценок (0–5). Выбирать из шести
    каждый раз утомительно, поэтому, как в Anki, оставлены четыре кнопки,
    и каждая соответствует одной оценке SM-2.
    """

    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"

    @property
    def label(self) -> str:
        return _GRADE_LABELS[self]

    @property
    def quality(self) -> int:
        """Оценка по шкале SM-2."""
        return _GRADE_QUALITY[self]


_GRADE_LABELS = {
    Grade.AGAIN: "Не помню",
    Grade.HARD: "С трудом",
    Grade.GOOD: "Хорошо",
    Grade.EASY: "Легко",
}

_GRADE_QUALITY = {
    Grade.AGAIN: 1,
    Grade.HARD: 3,
    Grade.GOOD: 4,
    Grade.EASY: 5,
}


@dataclass(frozen=True)
class Schedule:
    """Расписание карточки. frozen=True — объект нельзя изменить после создания."""

    repetitions: int = 0
    interval_days: int = 0
    ease_factor: float = DEFAULT_EASE_FACTOR


def next_schedule(current: Schedule, quality: int) -> Schedule:
    """Рассчитать новое расписание после ответа с оценкой quality (от 0 до 5)."""
    if not 0 <= quality <= 5:
        raise ValueError(f"Оценка должна быть от 0 до 5, получено: {quality}")

    if quality < PASSING_QUALITY:
        # Не вспомнил: серия успехов обнуляется, карточка вернётся завтра.
        repetitions = 0
        interval_days = 1
    else:
        if current.repetitions == 0:
            interval_days = 1  # первый успех — проверим завтра
        elif current.repetitions == 1:
            interval_days = 6  # второй успех — через шесть дней
        else:
            # Дальше интервал растёт умножением на «лёгкость»: 6 → 15 → 38 → …
            interval_days = round(current.interval_days * current.ease_factor)
        repetitions = current.repetitions + 1

    # Формула из описания SM-2. При оценке 5 «лёгкость» растёт на 0,1,
    # при 4 не меняется, при 3 падает на 0,14, при низких оценках падает сильнее.
    penalty = 5 - quality
    ease_factor = current.ease_factor + (0.1 - penalty * (0.08 + penalty * 0.02))
    ease_factor = max(MIN_EASE_FACTOR, ease_factor)

    return Schedule(repetitions=repetitions, interval_days=interval_days, ease_factor=ease_factor)
