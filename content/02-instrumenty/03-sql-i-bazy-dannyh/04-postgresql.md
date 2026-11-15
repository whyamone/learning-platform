---
title: 'PostgreSQL: серверная база данных'
summary: База данных, которую используют в большинстве настоящих проектов.
goal: Запустить PostgreSQL, создать базу и пользователя, подключиться из Python.
estimated_hours: 5
stub: true
concepts:
  - клиент и сервер базы данных
  - пользователи и права
  - утилита psql
  - транзакции
glossary:
  transaction: транзакция — набор изменений, выполняемый целиком
  commit: зафиксировать
  rollback: откатить
  connection: подключение
links:
  - title: Документация PostgreSQL на русском
    url: https://postgrespro.ru/docs/postgresql
    kind: docs
    lang: ru
  - title: Документация psycopg
    url: https://www.psycopg.org/psycopg3/docs/
    kind: docs
    lang: en
done_criteria:
  - Запустил PostgreSQL и перенёс в него учебную базу
  - Объясняю, чем серверная база отличается от SQLite
  - Понимаю, что такое транзакция
---

# Практика

Запусти PostgreSQL (в контейнере Docker или через `apt`), создай базу и пользователя, перенеси схему из прошлой темы. Подключись через `psql` и из Python. Покажи на примере, что делает откат транзакции.
