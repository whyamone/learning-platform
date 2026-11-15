---
title: Тестирование с pytest
summary: Как автоматически проверять, что код работает и не сломался после правок.
goal: Писать тесты для своих функций, использовать фикстуры и параметризацию.
estimated_hours: 7
stub: true
concepts:
  - тест и утверждение assert
  - фикстуры
  - параметризация
  - подмена зависимостей (mock)
  - покрытие кода
glossary:
  test: тест
  assert: утверждать
  fixture: фикстура — заготовка для теста
  mock: подделка, заменяющая настоящую зависимость
  coverage: покрытие
links:
  - title: Документация pytest — начало работы
    url: https://docs.pytest.org/en/stable/getting-started.html
    kind: docs
    lang: en
  - title: Хендбук по Python от Яндекса
    url: https://education.yandex.ru/handbook/python
    kind: course
    lang: ru
done_criteria:
  - Покрыл тестами проект logscan
  - Использую фикстуры и параметризацию
  - Тесты запускаются одной командой
---

# Практика

Напиши тесты для разбора строк и подсчётов в `logscan`: обычные случаи, пустой ввод, испорченные строки. Используй `tmp_path` для временных файлов и `pytest.mark.parametrize` для набора примеров. Посмотри, как устроены тесты этой платформы в папке `tests/`.
