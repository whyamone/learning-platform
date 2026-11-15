---
title: 'Асинхронность: async и await'
summary: Как выполнять много сетевых операций одновременно в одном потоке.
goal: Понимать, когда асинхронность нужна, и писать простые корутины.
estimated_hours: 7
stub: true
concepts:
  - конкурентность и параллелизм
  - корутина
  - цикл событий
  - asyncio.gather
  - блокирующий и неблокирующий код
glossary:
  async: асинхронный
  await: ждать результата, не блокируя остальных
  coroutine: корутина
  event loop: цикл событий
  concurrent: конкурентный
links:
  - title: Модуль asyncio — справочник
    url: https://docs.python.org/3/library/asyncio.html
    kind: docs
    lang: en
  - title: FastAPI — конкурентность и async / await
    url: https://fastapi.tiangolo.com/ru/async/
    kind: docs
    lang: ru
done_criteria:
  - Объясняю разницу между async def и def
  - Написал программу, которая опрашивает десять адресов одновременно
---

# Практика

Напиши программу, которая проверяет доступность списка сайтов: сначала последовательно, затем через `asyncio.gather` и `httpx.AsyncClient`. Измерь разницу во времени. Опиши, почему `time.sleep()` внутри корутины — ошибка.
