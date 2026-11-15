---
title: 'Dockerfile: свой образ'
summary: Как описать сборку образа для собственного приложения.
goal: Писать Dockerfile, собирать образ и понимать кэширование слоёв.
estimated_hours: 5
stub: true
concepts:
  - инструкции FROM, COPY, RUN, CMD
  - слои и кэш сборки
  - файл .dockerignore
  - размер образа
glossary:
  build: сборка
  layer: слой образа
  tag: метка версии
  base image: базовый образ
  entrypoint: точка входа
links:
  - title: Справочник по Dockerfile
    url: https://docs.docker.com/reference/dockerfile/
    kind: docs
    lang: en
  - title: Рекомендации по сборке образов
    url: https://docs.docker.com/build/building/best-practices/
    kind: docs
    lang: en
done_criteria:
  - Собрал образ своего сервиса и запустил его
  - Объясняю каждую строку Dockerfile этой платформы
  - Знаю, почему requirements.txt копируется раньше кода
---

# Практика

Напиши `Dockerfile` для сервиса «Инвентарь», собери и запусти. Измени одну строку кода и пересобери — посмотри, какие слои взяты из кэша. Сравни со сборкой, где код копируется раньше установки библиотек.
