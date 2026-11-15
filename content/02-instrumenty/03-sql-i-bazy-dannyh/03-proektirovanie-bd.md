---
title: Проектирование таблиц
summary: Как разложить данные по таблицам, чтобы они не противоречили друг другу.
goal: Проектировать схему из нескольких связанных таблиц с ключами и ограничениями.
estimated_hours: 4
stub: true
concepts:
  - первичный и внешний ключ
  - связи один-ко-многим и многие-ко-многим
  - нормализация
  - индексы
  - ограничения
glossary:
  primary key: первичный ключ
  foreign key: внешний ключ
  index: индекс — ускоряет поиск
  constraint: ограничение
  schema: схема базы
links:
  - title: Документация PostgreSQL на русском
    url: https://postgrespro.ru/docs/postgresql
    kind: docs
    lang: ru
  - title: Документация SQLite — CREATE TABLE
    url: https://www.sqlite.org/lang_createtable.html
    kind: docs
    lang: en
done_criteria:
  - Нарисовал схему из пяти таблиц и объяснил каждую связь
  - Разобрал схему базы этой платформы
---

# Практика

Спроектируй базу для учёта сети: площадки, устройства, интерфейсы, VLAN, связь интерфейсов с VLAN. Нарисуй схему, напиши команды `CREATE TABLE` с ключами и ограничениями. Сравни с таблицами этой платформы в `app/models/`.
