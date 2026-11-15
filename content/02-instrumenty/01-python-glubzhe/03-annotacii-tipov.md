---
title: Аннотации типов и dataclasses
summary: Как подписывать типы в коде и описывать структуры данных в несколько строк.
goal: Писать функции с аннотациями типов и использовать dataclass вместо словарей.
estimated_hours: 5
stub: true
concepts:
  - аннотации типов
  - Optional и объединение типов
  - декоратор dataclass
  - статическая проверка типов
glossary:
  type hint: подсказка типа
  annotation: аннотация
  optional: необязательный
  dataclass: класс данных
links:
  - title: Модуль typing — справочник
    url: https://docs.python.org/3/library/typing.html
    kind: docs
    lang: en
  - title: Модуль dataclasses — справочник
    url: https://docs.python.org/3/library/dataclasses.html
    kind: docs
    lang: en
done_criteria:
  - Все функции нового кода пишу с аннотациями
  - Заменил словарь с фиксированным набором ключей на dataclass
---

# Практика

Возьми проект `logscan` и добавь аннотации типов ко всем функциям. Запись журнала опиши как `@dataclass LogRecord`. Проверь код программой `mypy` или `pyright` и исправь замечания.
