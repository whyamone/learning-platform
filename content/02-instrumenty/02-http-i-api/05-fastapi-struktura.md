---
title: 'FastAPI: структура проекта и зависимости'
summary: Как организовать сервис, который растёт дальше одного файла.
goal: Разделять код на маршруты, сервисы и модели, использовать зависимости и настройки.
estimated_hours: 6
stub: true
concepts:
  - APIRouter
  - внедрение зависимостей Depends
  - настройки через переменные окружения
  - тестирование через TestClient
glossary:
  dependency: зависимость
  router: маршрутизатор — группа адресов
  settings: настройки
  lifespan: жизненный цикл приложения
links:
  - title: FastAPI — большие приложения
    url: https://fastapi.tiangolo.com/ru/tutorial/bigger-applications/
    kind: docs
    lang: ru
  - title: FastAPI — зависимости
    url: https://fastapi.tiangolo.com/ru/tutorial/dependencies/
    kind: docs
    lang: ru
done_criteria:
  - Сервис разложен на routers, services и models
  - Настройки читаются из .env
  - Есть тесты на основные адреса
---

# Практика

Разложи сервис «Инвентарь» по папкам так же, как устроена эта платформа. Вынеси настройки в `config.py`, напиши тесты через `TestClient`. Прочитай `docs/decisions.md` и объясни своими словами решение про три слоя.
