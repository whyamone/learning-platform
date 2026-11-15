---
title: 'SQL: выборка данных'
summary: Язык запросов, на котором разговаривают с базами данных.
goal: Писать запросы SELECT с фильтрами, сортировкой и ограничением.
estimated_hours: 6
stub: true
concepts:
  - таблица, строка, столбец
  - SELECT и WHERE
  - ORDER BY и LIMIT
  - INSERT, UPDATE, DELETE
  - значение NULL
glossary:
  table: таблица
  row: строка
  column: столбец
  query: запрос
  select: выбрать
links:
  - title: Интерактивный тренажёр по SQL (Stepik)
    url: https://stepik.org/course/63054/promo
    kind: course
    lang: ru
  - title: Документация SQLite — язык SQL
    url: https://www.sqlite.org/lang.html
    kind: docs
    lang: en
done_criteria:
  - Пишу запросы с несколькими условиями без подсказок
  - Добавляю, изменяю и удаляю строки
  - Открыл базу этой платформы и выполнил к ней запросы
---

# Практика

Установи `sqlite3`, создай базу с таблицей устройств и наполни её. Напиши двадцать запросов на выборку. Затем открой `data/app.db` этой платформы и найди все темы со статусом «готово».
