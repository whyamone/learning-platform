---
title: 'NumPy и pandas: работа с данными'
summary: Две главные библиотеки для числовых данных и таблиц.
goal: Загружать таблицы, фильтровать, группировать и считать статистику.
estimated_hours: 8
stub: true
concepts:
  - массив NumPy
  - таблица DataFrame
  - фильтрация и группировка
  - пропущенные значения
  - векторные операции
glossary:
  array: массив
  DataFrame: таблица данных в pandas
  series: столбец таблицы
  missing value: пропущенное значение
  aggregate: свести к итогу
links:
  - title: pandas за десять минут
    url: https://pandas.pydata.org/docs/user_guide/10min.html
    kind: docs
    lang: en
  - title: NumPy для начинающих
    url: https://numpy.org/doc/stable/user/absolute_beginners.html
    kind: docs
    lang: en
done_criteria:
  - Загружаю CSV и отвечаю на вопросы по данным
  - Группирую и считаю статистику без циклов
  - Строю простой график
---

# Практика

Преобразуй журнал событий из проекта `logscan` в таблицу pandas. Посчитай число событий по часам, устройствам и уровням, найди самый «шумный» час, построй график.
