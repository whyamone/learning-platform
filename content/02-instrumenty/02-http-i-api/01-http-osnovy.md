---
title: 'HTTP: как устроены запросы и ответы'
summary: Протокол, на котором работают сайты и почти все API.
goal: Читать запрос и ответ HTTP, понимать методы, заголовки и коды состояния.
estimated_hours: 4
stub: true
concepts:
  - запрос и ответ
  - методы GET, POST, PUT, DELETE
  - заголовки
  - коды состояния
  - REST
glossary:
  request: запрос
  response: ответ
  header: заголовок
  body: тело сообщения
  endpoint: адрес, на который отправляют запрос
links:
  - title: HTTP — обзор протокола (MDN)
    url: https://developer.mozilla.org/ru/docs/Web/HTTP
    kind: docs
    lang: ru
  - title: Документация curl
    url: https://curl.se/docs/manpage.html
    kind: docs
    lang: en
done_criteria:
  - Объясняю по выводу curl -v, что происходит на каждом шаге
  - Называю назначение пяти методов и десяти кодов состояния
---

# Практика

Через `curl -v` разбери запросы к трём открытым API. Для каждого выпиши метод, адрес, заголовки запроса, код и тип содержимого ответа. Отправь POST-запрос с JSON на сервис httpbin.org.
