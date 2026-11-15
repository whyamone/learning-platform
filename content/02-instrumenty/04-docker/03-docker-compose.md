---
title: 'Docker Compose: несколько сервисов'
summary: Как одной командой поднять приложение вместе с базой данных.
goal: Описывать несколько связанных сервисов в docker-compose.yml.
estimated_hours: 5
stub: true
concepts:
  - сервисы и сети Compose
  - переменные окружения
  - зависимости и проверки состояния
  - именованные тома
glossary:
  compose: составлять
  service: сервис
  network: сеть
  healthcheck: проверка состояния
  depends on: зависит от
links:
  - title: Документация Docker Compose
    url: https://docs.docker.com/compose/
    kind: docs
    lang: en
  - title: Справочник по файлу Compose
    url: https://docs.docker.com/reference/compose-file/
    kind: docs
    lang: en
done_criteria:
  - Поднял сервис вместе с PostgreSQL одной командой
  - Объясняю каждую строку docker-compose.yml этой платформы
---

# Практика

Напиши `docker-compose.yml` для сервиса «Инвентарь» и PostgreSQL: сеть, том для данных, переменные из `.env`, проверка состояния. Убедись, что сервис обращается к базе по имени сервиса, а не по адресу.
