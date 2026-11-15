---
title: Telegram-бот на aiogram
summary: Как написать бота, который отвечает на команды и сообщения.
goal: Создать бота, обрабатывать команды, текст и кнопки, хранить состояние диалога.
estimated_hours: 8
stub: true
concepts:
  - Bot API и токен
  - обработчики сообщений
  - клавиатуры и кнопки
  - машина состояний
  - long polling
glossary:
  bot: бот
  handler: обработчик
  update: обновление — событие от Telegram
  polling: опрос сервера
  state: состояние диалога
links:
  - title: Руководство по aiogram 3 на русском
    url: https://mastergroosha.github.io/aiogram-3-guide/
    kind: article
    lang: ru
  - title: Документация aiogram
    url: https://docs.aiogram.dev/en/latest/
    kind: docs
    lang: en
  - title: Telegram Bot API
    url: https://core.telegram.org/bots/api
    kind: docs
    lang: en
done_criteria:
  - Бот отвечает на команды и текст
  - Токен хранится в .env
  - Бот запускается в контейнере Docker
---

# Практика

Создай бота через BotFather. Реализуй команды `/start` и `/help`, эхо-ответ и меню с кнопками. Добавь команду `/subnet 192.168.1.0/26`, которая считает параметры подсети. Упакуй бота в Docker.
