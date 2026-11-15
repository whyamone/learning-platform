---
title: SQLAlchemy и миграции Alembic
summary: Как работать с базой через классы Python и менять её структуру без потери данных.
goal: Описывать модели, выполнять запросы через сеанс и вести миграции.
estimated_hours: 8
stub: true
concepts:
  - ORM
  - модель и сеанс
  - связи между моделями
  - миграция
  - автогенерация миграций
glossary:
  ORM: object-relational mapping — связь объектов Python с таблицами
  session: сеанс работы с базой
  migration: миграция — шаг изменения структуры базы
  relationship: связь между моделями
links:
  - title: SQLAlchemy — единый учебник
    url: https://docs.sqlalchemy.org/en/20/tutorial/
    kind: docs
    lang: en
  - title: Alembic — учебник
    url: https://alembic.sqlalchemy.org/en/latest/tutorial.html
    kind: docs
    lang: en
done_criteria:
  - Подключил базу к сервису «Инвентарь» вместо хранения в памяти
  - Изменил модель и создал миграцию
  - Читаю код app/models этой платформы без затруднений
---

# Практика

Подключи SQLAlchemy к сервису «Инвентарь»: модели устройств и интерфейсов со связью. Настрой Alembic, создай первую миграцию, затем добавь поле и вторую миграцию. Разбери папку `migrations/` этой платформы.
