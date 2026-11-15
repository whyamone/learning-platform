"""Вспомогательные заготовки для тестов: тексты тем и создание файлов."""

from pathlib import Path

# Маленькая учебная карта для тестов: 1 этап, 2 модуля, 3 темы.
PYTHON_TOPIC = """---
title: Переменные
summary: Как хранить данные.
goal: Научиться создавать переменные.
estimated_hours: 2.5
concepts:
  - переменная
  - присваивание
glossary:
  variable: переменная
links:
  - title: Учебник Python
    url: https://docs.python.org/3/tutorial/
    kind: docs
    lang: en
done_criteria:
  - Могу создать переменную
---

# Теория

Переменная — это **имя** для значения.

```python
# Практика  <- эта строка внутри кода, а не заголовок
answer = 42
```

# Практика

Создай переменную `name`.
"""

SIMPLE_TOPIC = """---
title: {title}
---

Текст темы «{title}».
"""


def write_file(path: Path, text: str) -> None:
    """Создать файл вместе с недостающими папками."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# Квиз и карточки к теме «Переменные» (файлы лежат рядом с файлом темы).
PYTHON_QUIZ = """- question: Что выведет print(7 // 2)?
  options:
    - 3
    - "3.5"
    - 4
  answer: 1
  explanation: Оператор // отбрасывает дробную часть.

- question: Каким знаком присваивают значение?
  options:
    - "=="
    - "="
  answer: 2
"""

PYTHON_CARDS = """- front: Что делает оператор //?
  back: Делит и **отбрасывает** дробную часть.

- front: Чем = отличается от ==?
  back: Первый присваивает, второй сравнивает.

- front: Какой тип у значения 3.14?
  back: float
"""
