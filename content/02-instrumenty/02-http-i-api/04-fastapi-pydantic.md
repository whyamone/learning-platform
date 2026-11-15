---
title: 'FastAPI: проверка данных через Pydantic'
summary: Как описать формат данных один раз и получить автоматическую проверку.
goal: Описывать модели запросов и ответов, проверять поля и возвращать понятные ошибки.
estimated_hours: 6
stub: true
concepts:
  - модель Pydantic
  - проверка полей
  - модели запроса и ответа
  - код 422
glossary:
  model: модель — описание структуры данных
  validation: проверка корректности
  schema: схема
  field: поле
links:
  - title: Документация Pydantic
    url: https://docs.pydantic.dev/latest/
    kind: docs
    lang: en
  - title: FastAPI — тело запроса
    url: https://fastapi.tiangolo.com/ru/tutorial/body/
    kind: docs
    lang: ru
done_criteria:
  - Все входные и выходные данные сервиса описаны моделями
  - Некорректный запрос получает ответ 422 с объяснением
---

# Практика

Добавь в сервис «Инвентарь» модели Pydantic: проверь формат IP-адреса, диапазон VLAN и длину имени. Раздели модели на «для создания», «для обновления» и «для ответа».
