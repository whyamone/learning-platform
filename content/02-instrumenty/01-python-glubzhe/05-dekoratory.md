---
title: Декораторы и контекстные менеджеры
summary: Как добавить поведение к функции, не меняя её код, и как гарантированно освобождать ресурсы.
goal: Понимать готовые декораторы и писать простые собственные.
estimated_hours: 5
stub: true
concepts:
  - функция как объект
  - декоратор
  - functools.wraps
  - контекстный менеджер и with
glossary:
  decorator: декоратор — обёртка над функцией
  wrapper: обёртка
  context manager: контекстный менеджер
  cache: кэш
links:
  - title: Глоссарий Python — декоратор
    url: https://docs.python.org/3/glossary.html#term-decorator
    kind: docs
    lang: en
  - title: Модуль contextlib — справочник
    url: https://docs.python.org/3/library/contextlib.html
    kind: docs
    lang: en
done_criteria:
  - Написал декоратор, измеряющий время работы функции
  - Объясняю, что делает @router.get в FastAPI
---

# Практика

Напиши декоратор `@timed`, печатающий время выполнения функции, и декоратор `@retry(times=3)`, повторяющий вызов при ошибке. Напиши контекстный менеджер `timer()` для использования через `with`.
