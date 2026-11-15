---
title: JSON и обмен данными
summary: Формат, на котором разговаривают почти все программы в интернете, включая API нейросетей.
goal: Читать и записывать JSON, превращать его в словари и списки Python и обратно.
estimated_hours: 4
concepts:
  - формат JSON
  - json.loads() и json.dumps()
  - json.load() и json.dump() для файлов
  - соответствие типов JSON и Python
glossary:
  JSON: JavaScript Object Notation — текстовый формат обмена данными
  load: загрузить (из файла)
  dump: выгрузить (в файл)
  loads: load string — загрузить из строки
  dumps: dump string — выгрузить в строку
  indent: отступ
  parse: разобрать текст на части
  serialize: превратить данные в текст для передачи или хранения
links:
  - title: Модуль json — справочник
    url: https://docs.python.org/3/library/json.html
    kind: docs
    lang: en
  - title: Описание формата JSON
    url: https://www.json.org/json-ru.html
    kind: docs
    lang: ru
done_criteria:
  - Отличаю словарь Python от строки с JSON
  - Читаю JSON из файла и из строки
  - Сохраняю данные в JSON-файл с отступами и русскими буквами
  - Достаю нужное значение из вложенного JSON
---

# Теория

## Что такое JSON

JSON — текстовый формат для передачи данных между программами. Когда ты
отправишь запрос к нейросети, ответ придёт именно в JSON. В нём же хранят
настройки и обмениваются данными сервисы.

```json
{
  "hostname": "sw-core-1",
  "ports": 48,
  "is_active": true,
  "location": null,
  "vlans": [10, 20, 30],
  "uplink": {"interface": "Gi0/1", "speed": 1000}
}
```

Выглядит почти как словарь Python — и это не случайно. Но есть отличия.

| JSON | Python |
|---|---|
| объект `{}` | словарь `dict` |
| массив `[]` | список `list` |
| строка `"text"` | `str` |
| число `48`, `3.5` | `int`, `float` |
| `true`, `false` | `True`, `False` |
| `null` | `None` |

Правила JSON строже: строки только в **двойных** кавычках, ключи — только строки,
запятая после последнего элемента запрещена, комментариев нет.

> JSON — это **текст**. Пока его не разобрали, это просто строка, из которой
> нельзя достать значение по ключу. Разбор превращает текст в словари и списки.

## Из строки в данные: json.loads()

```python
import json

text = '{"hostname": "sw-core-1", "ports": 48, "vlans": [10, 20]}'

data = json.loads(text)      # строка → словарь

print(type(text))            # <class 'str'>
print(type(data))            # <class 'dict'>
print(data["hostname"])      # sw-core-1
print(data["vlans"][0])      # 10
```

Буква `s` в `loads` означает string — «загрузить из строки».

## Из данных в строку: json.dumps()

```python
import json

device = {"hostname": "sw-core-1", "ports": 48, "is_active": True, "note": None}

text = json.dumps(device)
print(text)
# {"hostname": "sw-core-1", "ports": 48, "is_active": true, "note": null}
```

Обрати внимание: `True` стало `true`, а `None` — `null`.

Два параметра, которые нужны почти всегда:

```python
device = {"имя": "коммутатор", "порты": 48}

print(json.dumps(device))
# {"имя": "ком..."}  — русские буквы закодированы

print(json.dumps(device, ensure_ascii=False, indent=2))
```

```text
{
  "имя": "коммутатор",
  "порты": 48
}
```

- `ensure_ascii=False` — оставить русские буквы как есть;
- `indent=2` — красиво расставить отступы.

## Работа с файлами: json.load() и json.dump()

Те же функции без буквы `s` работают напрямую с файлом.

```python
import json

devices = [
    {"hostname": "sw-1", "ip": "192.168.1.1", "ports": 24},
    {"hostname": "sw-2", "ip": "192.168.1.2", "ports": 48},
]

# Запись в файл
with open("devices.json", "w", encoding="utf-8") as file:
    json.dump(devices, file, ensure_ascii=False, indent=2)

# Чтение из файла
with open("devices.json", encoding="utf-8") as file:
    loaded = json.load(file)

print(loaded[1]["hostname"])     # sw-2
```

Как запомнить четыре функции:

| | из/в строку | из/в файл |
|---|---|---|
| **текст → данные** | `json.loads(text)` | `json.load(file)` |
| **данные → текст** | `json.dumps(data)` | `json.dump(data, file)` |

## Ошибки разбора

Если текст не соответствует формату, возникает исключение:

```python
import json

try:
    data = json.loads("{'hostname': 'sw-1'}")    # одинарные кавычки — не JSON
except json.JSONDecodeError as error:
    print(f"Некорректный JSON: {error}")
```

Это пригодится при работе с нейросетями: модель может вернуть JSON с ошибкой,
и программа должна быть к этому готова.

## Пример: как выглядит ответ нейросети

Примерно такой JSON возвращает API языковой модели:

```python
import json

response_text = """
{
  "model": "example-model",
  "choices": [
    {
      "message": {"role": "assistant", "content": "VLAN — это виртуальная локальная сеть."},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 12, "completion_tokens": 9, "total_tokens": 21}
}
"""

response = json.loads(response_text)

answer = response["choices"][0]["message"]["content"]
tokens = response["usage"]["total_tokens"]

print(answer)
print(f"Потрачено токенов: {tokens}")
```

Разбери путь `response["choices"][0]["message"]["content"]` по шагам:
словарь → список → первый элемент → словарь → строка. Уметь так «ходить»
по вложенным данным — ежедневный навык AI-разработчика.

## Чего JSON не умеет

В JSON нельзя напрямую сохранить множество, кортеж (станет списком), дату
или объект своего класса. Их сначала превращают в подходящий тип:
множество — в список, дату — в строку.

# Практика

**Задание 1.** Создай словарь с описанием устройства (вложенный список
интерфейсов обязателен). Выведи его как JSON с отступами и русскими буквами.

**Задание 2.** Сохрани список из пяти устройств в файл `inventory.json`.
Открой файл командой `cat` и убедись, что он читается человеком.

**Задание 3.** Программа читает `inventory.json` и выводит таблицу устройств,
а затем — общее количество портов.

**Задание 4.** Программа-инвентарь с меню: показать устройства, добавить
устройство, удалить по имени, выйти. Данные хранятся в `inventory.json`
и сохраняются после каждого изменения. Если файла нет, программа начинает
с пустого списка.

**Задание 5.** Возьми пример ответа нейросети из теории, добавь в `choices`
второй элемент и выведи тексты всех ответов циклом.

**Задание 6 (со звёздочкой).** Программа читает `network.log` из темы
про файлы и сохраняет результат анализа в `summary.json`: количество записей
по уровням, по устройствам и список всех сообщений уровня `ERROR`.
