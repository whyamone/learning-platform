---
title: 'SQL: соединения и группировка'
summary: Как собирать данные из нескольких таблиц и считать итоги.
goal: Соединять таблицы через JOIN и строить отчёты через GROUP BY.
estimated_hours: 7
stub: true
concepts:
  - внутреннее и левое соединение
  - агрегатные функции
  - GROUP BY и HAVING
  - подзапросы
glossary:
  join: соединение таблиц
  group by: группировать по
  aggregate: агрегат — итог по группе строк
  subquery: вложенный запрос
links:
  - title: Интерактивный тренажёр по SQL (Stepik)
    url: https://stepik.org/course/63054/promo
    kind: course
    lang: ru
  - title: Документация PostgreSQL на русском
    url: https://postgrespro.ru/docs/postgresql
    kind: docs
    lang: ru
done_criteria:
  - Объясняю разницу между INNER JOIN и LEFT JOIN
  - Строю отчёт с группировкой по двум полям
---

# Практика

Добавь в учебную базу таблицы площадок и интерфейсов. Напиши запросы: устройства с названием площадки; количество интерфейсов по устройствам; площадки без устройств; три самых загруженных устройства.
