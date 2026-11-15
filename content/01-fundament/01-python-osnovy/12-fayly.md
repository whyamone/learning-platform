---
title: Работа с файлами
summary: Чтение и запись текстовых файлов — чтобы данные жили дольше, чем программа.
goal: Читать файлы целиком и построчно, записывать результаты и работать с путями через pathlib.
estimated_hours: 5
concepts:
  - функция open() и режимы доступа
  - конструкция with
  - построчное чтение
  - кодировка UTF-8
  - модуль pathlib
glossary:
  open: открыть
  read: читать
  write: писать
  close: закрыть
  path: путь
  encoding: кодировка
  mode: режим
  exists: существует
links:
  - title: Официальный учебник — чтение и запись файлов
    url: https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files
    kind: docs
    lang: en
  - title: Модуль pathlib — справочник
    url: https://docs.python.org/3/library/pathlib.html
    kind: docs
    lang: en
done_criteria:
  - Читаю файл целиком и построчно
  - Записываю и дописываю текст в файл
  - Всегда открываю файлы через with и указываю кодировку
  - Проверяю существование файла и перебираю файлы в папке через pathlib
---

# Теория

## Открытие файла

Пока программа работает, данные лежат в переменных. Когда она завершается,
переменные исчезают. Чтобы сохранить результат, его записывают в файл.

Подготовь файл для опытов:

```bash
cd ~/study/python
printf "sw-1 192.168.1.1\nsw-2 192.168.1.2\nrouter-1 192.168.1.254\n" > devices.txt
```

Чтение файла целиком:

```python
with open("devices.txt", encoding="utf-8") as file:
    text = file.read()

print(text)
```

Что здесь происходит:

- `open()` открывает файл и возвращает объект для работы с ним;
- `as file` даёт этому объекту имя;
- `with` гарантирует, что файл закроется, когда блок закончится —
  даже если внутри произойдёт ошибка;
- `encoding="utf-8"` указывает кодировку.

> Всегда указывай `encoding="utf-8"`. Без этого Python возьмёт кодировку
> системы, и на Windows русский текст превратится в «кракозябры».

## Построчное чтение

Большие файлы (например, логи на гигабайт) не читают целиком — не хватит
памяти. Файл можно перебирать циклом по одной строке:

```python
with open("devices.txt", encoding="utf-8") as file:
    for line in file:
        line = line.strip()          # убрать перевод строки в конце
        if not line:
            continue                 # пропустить пустые строки
        name, ip = line.split()
        print(f"{name:10} -> {ip}")
```

Каждая строка из файла заканчивается символом `\n`. Поэтому почти всегда
первым делом вызывают `strip()`.

Если файл небольшой и строки нужны списком:

```python
with open("devices.txt", encoding="utf-8") as file:
    lines = file.read().splitlines()

print(len(lines))     # 3
```

## Режимы открытия

Второй аргумент `open()` задаёт режим.

| Режим | Что делает | Если файла нет | Если файл есть |
|---|---|---|---|
| `"r"` | чтение (по умолчанию) | ошибка | читает |
| `"w"` | запись | создаёт | **стирает** и пишет заново |
| `"a"` | дозапись в конец | создаёт | дописывает |

## Запись в файл

```python
devices = ["sw-1", "sw-2", "router-1"]

with open("report.txt", "w", encoding="utf-8") as file:
    file.write("Отчёт по устройствам\n")
    for device in devices:
        file.write(f"{device}: проверено\n")
```

`write()` не добавляет перевод строки сам — символ `\n` ставь вручную.

Дозапись, например ведение журнала:

```python
with open("history.log", "a", encoding="utf-8") as file:
    file.write("Проверка выполнена\n")
```

> Режим `"w"` молча уничтожает прежнее содержимое. Перепутаешь `"w"` и `"r"`,
> открывая важный файл, — потеряешь данные.

## Если файла нет

```python
with open("missing.txt", encoding="utf-8") as file:
    text = file.read()
```

```text
FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'
```

Относительный путь отсчитывается от папки, **из которой запущена программа**,
а не от папки, где лежит файл с кодом. Это частая причина такой ошибки.

## Модуль pathlib

Современный способ работать с путями — объект `Path`.

```python
from pathlib import Path

path = Path("devices.txt")

print(path.exists())      # True — существует ли
print(path.is_file())     # True — это файл, а не папка
print(path.name)          # devices.txt
print(path.suffix)        # .txt — расширение
print(path.stem)          # devices — имя без расширения
print(path.resolve())     # полный абсолютный путь
```

Пути собираются оператором `/` — он работает одинаково в Linux и Windows:

```python
logs_dir = Path.home() / "study" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)     # создать папку, если её нет

report = logs_dir / "report.txt"
```

У `Path` есть короткие методы для чтения и записи целиком:

```python
report.write_text("Готово\n", encoding="utf-8")
print(report.read_text(encoding="utf-8"))
```

Перебор файлов в папке:

```python
for path in Path(".").glob("*.py"):
    print(path.name)
```

`glob("*.py")` находит все файлы с расширением `.py`. Вариант `rglob`
ищет ещё и во вложенных папках.

## Пример: анализ лога

```python
from pathlib import Path


def count_levels(path):
    """Посчитать, сколько строк каждого уровня в файле лога."""
    counts = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            parts = line.split()
            if len(parts) < 4:
                continue                    # строка не похожа на запись лога
            level = parts[3]
            counts[level] = counts.get(level, 0) + 1
    return counts


log_path = Path("network.log")
if log_path.exists():
    for level, count in count_levels(log_path).items():
        print(f"{level}: {count}")
else:
    print(f"Файл {log_path} не найден")
```

Здесь сошлись почти все прошлые темы: функции, циклы, строки, словари.

# Практика

Сначала создай файл `network.log` из 15–20 строк такого вида (уровни `INFO`,
`WARNING`, `ERROR`, устройства разные):

```text
2026-01-15 14:32:07 sw-core-1 ERROR Port Gi0/5 is down
2026-01-15 14:32:09 sw-core-1 INFO Port Gi0/6 is up
```

**Задание 1.** Выведи количество строк в файле и первые пять строк.

**Задание 2.** Выведи только строки уровня `ERROR`. Сохрани их в файл `errors.log`.

**Задание 3.** Посчитай, сколько сообщений каждого уровня и сколько сообщений
от каждого устройства.

**Задание 4.** Создай файл `devices.txt` со строками `имя ip`. Программа читает
его в список словарей и записывает отчёт в `report.txt`: по одной строке
на устройство плюс итоговая строка с количеством.

**Задание 5.** Программа-блокнот: запрашивает строку и дописывает её в `notes.txt`
вместе с текущей датой и временем. При следующем запуске прежние записи
должны остаться на месте.

**Задание 6 (со звёздочкой).** Программа обходит папку `~/study` со всеми
вложенными папками и выводит для каждого файла `.py` его имя и количество строк,
а в конце — общее количество строк кода, которое ты уже написал.
