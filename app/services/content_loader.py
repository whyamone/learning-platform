"""Чтение учебных материалов из папки content/.

Этот файл ничего не знает о базе данных: он только читает файлы и
возвращает их содержимое в виде простых Python-объектов. Запись в базу —
задача соседнего файла importer.py. Так каждую часть проще понять и проверить.

Ожидаемая структура папки:

    content/
      01-fundament/              ← этап: номер + имя латиницей
        stage.yaml               ← название и описание этапа
        01-python-osnovy/        ← модуль
          module.yaml
          01-pervaya-programma.md          ← тема: «шапка» YAML + текст Markdown
          01-pervaya-programma.quiz.yaml   ← вопросы квиза (необязательно)
          01-pervaya-programma.cards.yaml  ← карточки для повторения (необязательно)

Если в файле ошибка, он пропускается, а сообщение об ошибке попадает
в список `problems` и показывается на странице дорожной карты.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Имя папки или файла: «01-pervaya-programma» → номер 1 и slug «pervaya-programma».
NAME_PATTERN = re.compile(r"^(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)$")

# Заголовки, по которым текст темы делится на теорию и практику.
THEORY_HEADING = "# теория"
PRACTICE_HEADING = "# практика"

ALLOWED_STAGE_KEYS = {"title", "description", "month_from", "month_to"}
ALLOWED_MODULE_KEYS = {"title", "description"}
ALLOWED_TOPIC_KEYS = {
    "title",
    "summary",
    "goal",
    "estimated_hours",
    "concepts",
    "glossary",
    "links",
    "done_criteria",
    "stub",
}
ALLOWED_QUESTION_KEYS = {"question", "options", "answer", "explanation"}
ALLOWED_CARD_KEYS = {"front", "back"}
MIN_OPTIONS = 2
MAX_OPTIONS = 6
ALLOWED_LINK_KINDS = {"docs", "article", "course", "video", "book", "practice"}
ALLOWED_LINK_LANGS = {"ru", "en"}


class ContentFormatError(Exception):
    """Ошибка в файле с материалами. Текст ошибки показывается пользователю."""


# --- Объекты, в которые превращаются файлы -------------------------------------
# dataclass — короткий способ описать класс, который просто хранит данные.


@dataclass
class LinkData:
    title: str
    url: str
    kind: str = "article"
    lang: str = "ru"


@dataclass
class QuestionData:
    text: str
    options: list[str]
    correct_index: int  # счёт с нуля; в файле для удобства пишется с единицы
    explanation: str = ""


@dataclass
class CardData:
    front: str
    back: str


@dataclass
class TopicData:
    slug: str
    position: int
    title: str
    source_path: str
    summary: str = ""
    goal: str = ""
    estimated_hours: float = 2.0
    concepts: list[str] = field(default_factory=list)
    glossary: list[dict[str, str]] = field(default_factory=list)
    done_criteria: list[str] = field(default_factory=list)
    links: list[LinkData] = field(default_factory=list)
    theory_md: str = ""
    practice_md: str = ""
    is_stub: bool = False
    questions: list[QuestionData] = field(default_factory=list)
    cards: list[CardData] = field(default_factory=list)


@dataclass
class ModuleData:
    slug: str
    position: int
    title: str
    description: str = ""
    topics: list[TopicData] = field(default_factory=list)


@dataclass
class StageData:
    slug: str
    position: int
    title: str
    description: str = ""
    month_from: int = 1
    month_to: int = 1
    modules: list[ModuleData] = field(default_factory=list)


@dataclass
class ContentProblem:
    """Замечание к файлу: где и что не так."""

    path: str
    message: str


@dataclass
class LoadResult:
    stages: list[StageData] = field(default_factory=list)
    problems: list[ContentProblem] = field(default_factory=list)


# --- Главная функция ------------------------------------------------------------


def load_content(content_dir: Path) -> LoadResult:
    """Прочитать всю папку с материалами."""
    result = LoadResult()

    if not content_dir.is_dir():
        result.problems.append(ContentProblem(str(content_dir), "Папка с материалами не найдена."))
        return result

    # Запоминаем, какой slug в каком файле встретился, чтобы найти повторы.
    seen_slugs: dict[str, dict[str, str]] = {"stage": {}, "module": {}, "topic": {}}

    def relative(path: Path) -> str:
        """Путь относительно content/ — в таком виде его удобно показывать."""
        return path.relative_to(content_dir).as_posix()

    def is_duplicate(kind: str, slug: str, path: Path) -> bool:
        """Проверить, не встречалось ли уже такое имя, и сообщить о повторе."""
        first_path = seen_slugs[kind].get(slug)
        if first_path is not None:
            result.problems.append(
                ContentProblem(
                    relative(path),
                    f"Имя «{slug}» уже используется в «{first_path}». Переименуй одно из них.",
                )
            )
            return True
        seen_slugs[kind][slug] = relative(path)
        return False

    for stage_dir in _numbered_children(content_dir, result, relative, only_dirs=True):
        position, slug = _parse_name(stage_dir.name)
        try:
            stage = _load_stage(stage_dir, position, slug, result, relative)
        except ContentFormatError as error:
            result.problems.append(ContentProblem(relative(stage_dir), str(error)))
            continue
        if is_duplicate("stage", slug, stage_dir):
            continue
        result.stages.append(stage)

        for module_dir in _numbered_children(stage_dir, result, relative, only_dirs=True):
            position, slug = _parse_name(module_dir.name)
            try:
                module = _load_module(module_dir, position, slug, result, relative)
            except ContentFormatError as error:
                result.problems.append(ContentProblem(relative(module_dir), str(error)))
                continue
            if is_duplicate("module", slug, module_dir):
                continue
            stage.modules.append(module)

            for topic_file in _numbered_children(module_dir, result, relative, only_dirs=False):
                position, slug = _parse_name(topic_file.stem)
                try:
                    topic = _load_topic(topic_file, position, slug, result, relative)
                except ContentFormatError as error:
                    result.problems.append(ContentProblem(relative(topic_file), str(error)))
                    continue
                if is_duplicate("topic", slug, topic_file):
                    continue
                module.topics.append(topic)

    return result


# --- Поиск папок и файлов -------------------------------------------------------


def _parse_name(name: str) -> tuple[int, str]:
    """Разобрать имя «01-python-osnovy» на номер 1 и slug «python-osnovy»."""
    match = NAME_PATTERN.match(name)
    if match is None:
        raise ContentFormatError(
            "Имя должно состоять из номера, дефиса и слов латиницей в нижнем регистре, "
            "например «01-python-osnovy»."
        )
    return int(match.group(1)), match.group(2)


def _numbered_children(
    folder: Path, result: LoadResult, relative, *, only_dirs: bool
) -> list[Path]:
    """Вернуть вложенные папки (или .md-файлы) с правильными именами, по порядку номеров."""
    children: list[tuple[int, Path]] = []

    for child in sorted(folder.iterdir()):
        if child.name.startswith("."):
            continue  # служебные файлы вроде .gitkeep
        if only_dirs:
            if not child.is_dir():
                continue
            name = child.name
        else:
            if child.is_dir() or child.suffix != ".md":
                continue
            name = child.stem  # имя файла без расширения .md

        try:
            position, _slug = _parse_name(name)
        except ContentFormatError as error:
            result.problems.append(ContentProblem(relative(child), str(error)))
            continue
        children.append((position, child))

    children.sort(key=lambda pair: pair[0])
    return [child for _position, child in children]


# --- Чтение этапа, модуля и темы ------------------------------------------------


def _load_stage(stage_dir: Path, position: int, slug: str, result, relative) -> StageData:
    meta_path = stage_dir / "stage.yaml"
    meta = _read_yaml_file(meta_path)
    _report_unknown_keys(meta, ALLOWED_STAGE_KEYS, relative(meta_path), result)

    month_from = _get_int(meta, "month_from", default=1)
    month_to = _get_int(meta, "month_to", default=month_from)
    if month_to < month_from:
        raise ContentFormatError("«month_to» не может быть меньше «month_from».")

    return StageData(
        slug=slug,
        position=position,
        title=_get_text(meta, "title", required=True),
        description=_get_text(meta, "description"),
        month_from=month_from,
        month_to=month_to,
    )


def _load_module(module_dir: Path, position: int, slug: str, result, relative) -> ModuleData:
    meta_path = module_dir / "module.yaml"
    meta = _read_yaml_file(meta_path)
    _report_unknown_keys(meta, ALLOWED_MODULE_KEYS, relative(meta_path), result)

    return ModuleData(
        slug=slug,
        position=position,
        title=_get_text(meta, "title", required=True),
        description=_get_text(meta, "description"),
    )


def _load_topic(topic_file: Path, position: int, slug: str, result, relative) -> TopicData:
    meta, body = _split_front_matter(_read_text(topic_file))
    _report_unknown_keys(meta, ALLOWED_TOPIC_KEYS, relative(topic_file), result)
    theory_md, practice_md = _split_body(body)

    cards_path = topic_file.with_name(f"{topic_file.stem}.cards.yaml")

    hours = meta.get("estimated_hours", 2.0)
    # bool — тоже число для Python (True == 1), поэтому исключаем его отдельно.
    if isinstance(hours, bool) or not isinstance(hours, int | float) or hours <= 0:
        raise ContentFormatError("«estimated_hours» должно быть числом больше нуля, например 2.5.")

    return TopicData(
        slug=slug,
        position=position,
        source_path=relative(topic_file),
        title=_get_text(meta, "title", required=True),
        summary=_get_text(meta, "summary"),
        goal=_get_text(meta, "goal"),
        estimated_hours=float(hours),
        concepts=_get_text_list(meta, "concepts"),
        glossary=_get_glossary(meta),
        done_criteria=_get_text_list(meta, "done_criteria"),
        links=_get_links(meta),
        theory_md=theory_md,
        practice_md=practice_md,
        is_stub=_get_bool(meta, "stub"),
        questions=_load_optional_list(
            topic_file.with_name(f"{topic_file.stem}.quiz.yaml"), _parse_question, result, relative
        ),
        cards=_drop_duplicate_cards(
            _load_optional_list(cards_path, _parse_card, result, relative),
            relative(cards_path),
            result,
        ),
    )


# --- Квизы и карточки -----------------------------------------------------------


def _load_optional_list(path: Path, parse_item, result, relative) -> list:
    """Прочитать необязательный файл со списком вопросов или карточек.

    Файла может не быть — это нормально, вернётся пустой список. Ошибка
    в отдельном вопросе не отменяет остальные: плохой элемент пропускается,
    а замечание попадает в общий список.
    """
    if not path.exists():
        return []

    try:
        data = yaml.safe_load(_read_text(path))
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f" (строка {mark.line + 1})" if mark is not None else ""
        message = f"Ошибка в YAML{where}: проверь отступы, двоеточия и кавычки."
        result.problems.append(ContentProblem(relative(path), message))
        return []
    except ContentFormatError as error:
        result.problems.append(ContentProblem(relative(path), str(error)))
        return []

    if data is None:
        return []
    if not isinstance(data, list):
        result.problems.append(
            ContentProblem(relative(path), "Файл должен быть списком: каждый элемент с дефиса.")
        )
        return []

    items = []
    for number, raw_item in enumerate(data, start=1):
        try:
            items.append(parse_item(raw_item))
        except ContentFormatError as error:
            result.problems.append(ContentProblem(relative(path), f"Элемент №{number}: {error}"))
    return items


def _drop_duplicate_cards(cards: list[CardData], path: str, result) -> list[CardData]:
    """Убрать карточки с одинаковым вопросом: расписание хранится по тексту вопроса."""
    seen: set[str] = set()
    unique: list[CardData] = []
    for card in cards:
        normalized = " ".join(card.front.lower().split())
        if normalized in seen:
            result.problems.append(
                ContentProblem(path, f"Карточка с вопросом «{card.front}» встречается дважды.")
            )
            continue
        seen.add(normalized)
        unique.append(card)
    return unique


def _require_mapping(raw: Any, allowed_keys: set[str]) -> dict[str, Any]:
    """Проверить, что элемент списка — набор полей и что лишних полей нет."""
    if not isinstance(raw, dict):
        raise ContentFormatError("ожидались поля в формате «ключ: значение».")
    unknown = sorted(str(key) for key in raw if key not in allowed_keys)
    if unknown:
        allowed = ", ".join(sorted(allowed_keys))
        raise ContentFormatError(f"неизвестные поля: {', '.join(unknown)}. Допустимые: {allowed}.")
    return raw


def _plain_text(value: Any, field_name: str) -> str:
    """Превратить значение из YAML в строку.

    YAML сам угадывает типы: `3` он прочитает как число, а `yes` и `no` —
    как «истину» и «ложь». Числа безопасно превратить обратно в текст,
    а вот `yes` уже потерян — поэтому просим взять такое значение в кавычки.
    """
    if isinstance(value, bool) or value is None:
        raise ContentFormatError(
            f"поле «{field_name}»: возьми значение в кавычки, иначе YAML читает его не как текст."
        )
    if not isinstance(value, str | int | float):
        raise ContentFormatError(f"поле «{field_name}» должно быть текстом.")
    text = str(value).strip()
    if not text:
        raise ContentFormatError(f"поле «{field_name}» не должно быть пустым.")
    return text


def _parse_question(raw: Any) -> QuestionData:
    item = _require_mapping(raw, ALLOWED_QUESTION_KEYS)

    options_raw = item.get("options")
    if not isinstance(options_raw, list) or not MIN_OPTIONS <= len(options_raw) <= MAX_OPTIONS:
        raise ContentFormatError(
            f"в «options» должно быть от {MIN_OPTIONS} до {MAX_OPTIONS} вариантов ответа."
        )
    options = [_plain_text(option, "options") for option in options_raw]
    if len(set(options)) != len(options):
        raise ContentFormatError("варианты ответа не должны повторяться.")

    answer = item.get("answer")
    if isinstance(answer, bool) or not isinstance(answer, int) or not 1 <= answer <= len(options):
        raise ContentFormatError(
            f"«answer» — номер правильного варианта, число от 1 до {len(options)}."
        )

    explanation = item.get("explanation")
    return QuestionData(
        text=_plain_text(item.get("question"), "question"),
        options=options,
        correct_index=answer - 1,
        explanation="" if explanation is None else _plain_text(explanation, "explanation"),
    )


def _parse_card(raw: Any) -> CardData:
    item = _require_mapping(raw, ALLOWED_CARD_KEYS)
    return CardData(
        front=_plain_text(item.get("front"), "front"),
        back=_plain_text(item.get("back"), "back"),
    )


# --- Разбор текста --------------------------------------------------------------


def _read_text(path: Path) -> str:
    """Прочитать файл как текст.

    Кодировка «utf-8-sig» понимает и обычный UTF-8, и UTF-8 с невидимой
    меткой в начале файла — её любит добавлять «Блокнот» в Windows.
    """
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ContentFormatError(f"Не найден файл «{path.name}».") from None
    except UnicodeDecodeError:
        raise ContentFormatError("Файл сохранён не в кодировке UTF-8.") from None


def _parse_yaml(text: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        # У ошибок YAML есть место, где парсер споткнулся, — покажем номер строки.
        mark = getattr(error, "problem_mark", None)
        where = f" (строка {mark.line + 1})" if mark is not None else ""
        raise ContentFormatError(f"Ошибка в YAML{where}: проверь отступы и двоеточия.") from None

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ContentFormatError("Ожидался список полей в формате «ключ: значение».")
    return data


def _read_yaml_file(path: Path) -> dict[str, Any]:
    return _parse_yaml(_read_text(path))


def _split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Разделить файл темы на «шапку» (YAML между строками ---) и основной текст."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ContentFormatError("Файл должен начинаться со строки «---» (начало шапки).")

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            meta = _parse_yaml("\n".join(lines[1:index]))
            body = "\n".join(lines[index + 1 :])
            return meta, body

    raise ContentFormatError("Не найдена вторая строка «---», которая закрывает шапку.")


def _split_body(body: str) -> tuple[str, str]:
    """Разделить текст на теорию и практику по заголовку «# Практика».

    Строки внутри блоков кода (между ```) не считаются заголовками:
    в коде на Python строка с «#» — это комментарий.
    """
    theory_lines: list[str] = []
    practice_lines: list[str] = []
    current = theory_lines
    inside_code_block = False

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            inside_code_block = not inside_code_block

        if not inside_code_block:
            if stripped.lower() == THEORY_HEADING:
                continue  # сам заголовок не нужен: страница добавит свой
            if stripped.lower() == PRACTICE_HEADING:
                current = practice_lines
                continue

        current.append(line)

    return "\n".join(theory_lines).strip(), "\n".join(practice_lines).strip()


# --- Проверка полей шапки -------------------------------------------------------


def _report_unknown_keys(meta: dict[str, Any], allowed: set[str], path: str, result) -> None:
    """Сообщить о полях, которых мы не знаем: чаще всего это опечатки."""
    unknown = sorted(str(key) for key in meta if key not in allowed)
    if unknown:
        result.problems.append(
            ContentProblem(
                path,
                f"Неизвестные поля: {', '.join(unknown)}. "
                f"Допустимые: {', '.join(sorted(allowed))}.",
            )
        )


def _get_text(meta: dict[str, Any], key: str, *, required: bool = False) -> str:
    value = meta.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ContentFormatError(f"Не заполнено обязательное поле «{key}».")
        return ""
    if not isinstance(value, str | int | float):
        raise ContentFormatError(f"Поле «{key}» должно быть текстом.")
    return str(value).strip()


def _get_int(meta: dict[str, Any], key: str, *, default: int) -> int:
    value = meta.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContentFormatError(f"Поле «{key}» должно быть целым числом от 1.")
    return value


def _get_bool(meta: dict[str, Any], key: str) -> bool:
    value = meta.get(key, False)
    if not isinstance(value, bool):
        raise ContentFormatError(f"Поле «{key}» должно быть true или false.")
    return value


def _get_text_list(meta: dict[str, Any], key: str) -> list[str]:
    value = meta.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str | int | float) for item in value
    ):
        raise ContentFormatError(f"Поле «{key}» должно быть списком строк (каждая с дефиса).")
    return [str(item).strip() for item in value]


def _get_glossary(meta: dict[str, Any]) -> list[dict[str, str]]:
    """Словарик терминов: в файле «термин: перевод», в результате — список пар."""
    value = meta.get("glossary")
    if value is None:
        return []
    if not isinstance(value, dict):
        raise ContentFormatError("Поле «glossary» должно быть списком пар «термин: перевод».")
    return [{"term": str(term), "meaning": str(meaning)} for term, meaning in value.items()]


def _get_links(meta: dict[str, Any]) -> list[LinkData]:
    value = meta.get("links")
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContentFormatError("Поле «links» должно быть списком ссылок.")

    links: list[LinkData] = []
    for number, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ContentFormatError(f"Ссылка №{number}: ожидались поля title и url.")

        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        kind = str(item.get("kind") or "article").strip()
        lang = str(item.get("lang") or "ru").strip()

        if not title or not url:
            raise ContentFormatError(f"Ссылка №{number}: нужны оба поля — title и url.")
        if not url.startswith(("http://", "https://")):
            raise ContentFormatError(
                f"Ссылка №{number}: url должен начинаться с http:// или https://."
            )
        if kind not in ALLOWED_LINK_KINDS:
            allowed = ", ".join(sorted(ALLOWED_LINK_KINDS))
            raise ContentFormatError(
                f"Ссылка №{number}: kind «{kind}» неизвестен. Варианты: {allowed}."
            )
        if lang not in ALLOWED_LINK_LANGS:
            raise ContentFormatError(f"Ссылка №{number}: lang должен быть ru или en.")

        links.append(LinkData(title=title, url=url, kind=kind, lang=lang))
    return links
