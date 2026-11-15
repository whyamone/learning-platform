---
title: Работа с LLM через API
summary: Как отправить запрос модели из программы и разобрать ответ.
goal: Вызывать модели через OpenAI-совместимый API, вести диалог и управлять параметрами.
estimated_hours: 8
stub: true
concepts:
  - формат chat completions
  - роли system, user, assistant
  - история сообщений
  - параметры max_tokens и temperature
  - учёт токенов
glossary:
  completion: завершение — ответ модели
  role: роль автора сообщения
  message: сообщение
  usage: расход токенов
  API key: ключ доступа к API
links:
  - title: Документация Ollama
    url: https://docs.ollama.com/
    kind: docs
    lang: en
  - title: Документация OpenAI API
    url: https://platform.openai.com/docs/
    kind: docs
    lang: en
  - title: Документация Claude API
    url: https://platform.claude.com/docs/
    kind: docs
    lang: en
done_criteria:
  - Отправляю запрос модели из Python и получаю ответ
  - Веду многоходовый диалог, передавая историю
  - Один и тот же код работает с локальной и облачной моделью
---

# Практика

Напиши консольный чат с локальной моделью через её OpenAI-совместимый API: история диалога, системный промпт из файла, вывод числа потраченных токенов. Сделай адрес сервера и имя модели настройками, чтобы код работал с любым совместимым сервисом.
