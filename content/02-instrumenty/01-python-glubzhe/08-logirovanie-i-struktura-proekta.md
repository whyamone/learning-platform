---
title: Логирование и структура проекта
summary: Как заменить отладочные print() на журнал и разложить код по папкам.
goal: Настраивать модуль logging и оформлять проект как пакет с pyproject.toml.
estimated_hours: 4
stub: true
concepts:
  - уровни логирования
  - настройка logging
  - пакет и файл __init__.py
  - pyproject.toml
glossary:
  logging: журналирование
  level: уровень
  handler: обработчик — куда пишется журнал
  package: пакет
links:
  - title: Logging HOWTO — руководство по логированию
    url: https://docs.python.org/3/howto/logging.html
    kind: docs
    lang: en
  - title: Python Packaging User Guide
    url: https://packaging.python.org/en/latest/
    kind: docs
    lang: en
done_criteria:
  - В моих программах нет отладочных print() — только logging
  - Проект разложен по модулям и запускается как пакет
---

# Практика

Замени в `logscan` все служебные `print()` на `logging` с уровнями и опцией `--verbose`. Разложи код по папке-пакету, добавь `pyproject.toml` с настройками `ruff` и `pytest`.
