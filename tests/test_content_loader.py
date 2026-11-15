"""Тесты чтения учебных материалов из файлов."""

from pathlib import Path

from app.config import BASE_DIR
from app.services.content_loader import load_content
from tests.helpers import SIMPLE_TOPIC, write_file


def problem_messages(result) -> str:
    """Все замечания одной строкой — так удобнее искать нужный текст."""
    return " | ".join(f"{problem.path}: {problem.message}" for problem in result.problems)


def test_loads_stages_modules_and_topics_in_order(content_dir: Path):
    result = load_content(content_dir)

    assert result.problems == []
    assert [stage.slug for stage in result.stages] == ["fundament"]

    stage = result.stages[0]
    assert (stage.title, stage.month_from, stage.month_to) == ("Фундамент", 1, 4)
    assert [module.slug for module in stage.modules] == ["python", "linux"]
    assert [topic.slug for topic in stage.modules[0].topics] == ["peremennye", "usloviya"]


def test_reads_all_topic_fields(content_dir: Path):
    topic = load_content(content_dir).stages[0].modules[0].topics[0]

    assert topic.title == "Переменные"
    assert topic.position == 1
    assert topic.estimated_hours == 2.5
    assert topic.concepts == ["переменная", "присваивание"]
    assert topic.glossary == [{"term": "variable", "meaning": "переменная"}]
    assert topic.done_criteria == ["Могу создать переменную"]
    assert topic.links[0].url == "https://docs.python.org/3/tutorial/"
    assert topic.links[0].lang == "en"
    assert topic.source_path == "01-fundament/01-python/01-peremennye.md"


def test_splits_body_into_theory_and_practice(content_dir: Path):
    topic = load_content(content_dir).stages[0].modules[0].topics[0]

    assert topic.theory_md.startswith("Переменная — это")
    assert topic.practice_md == "Создай переменную `name`."
    # Строка «# Практика» внутри блока кода — комментарий, а не заголовок раздела.
    assert "answer = 42" in topic.theory_md


def test_topic_without_practice_heading_is_all_theory(content_dir: Path):
    topic = load_content(content_dir).stages[0].modules[0].topics[1]

    assert topic.theory_md == "Текст темы «Условия»."
    assert topic.practice_md == ""


def test_numbers_define_order_not_alphabet(content_dir: Path):
    module = content_dir / "01-fundament" / "01-python"
    write_file(module / "10-cikly.md", SIMPLE_TOPIC.format(title="Циклы"))
    write_file(module / "9-spiski.md", SIMPLE_TOPIC.format(title="Списки"))

    topics = load_content(content_dir).stages[0].modules[0].topics

    # По алфавиту «10-…» шло бы раньше «9-…», но мы сортируем по числу.
    assert [topic.slug for topic in topics][-2:] == ["spiski", "cikly"]


def test_file_with_windows_bom_is_read(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "03-bom.md"
    # «Блокнот» в Windows добавляет в начало файла невидимую метку (BOM).
    path.write_text(SIMPLE_TOPIC.format(title="С меткой"), encoding="utf-8-sig")

    result = load_content(content_dir)

    assert result.problems == []
    assert result.stages[0].modules[0].topics[-1].title == "С меткой"


def test_missing_title_is_reported_and_topic_skipped(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "03-bez-nazvaniya.md"
    write_file(path, "---\nsummary: без названия\n---\nТекст\n")

    result = load_content(content_dir)

    assert "03-bez-nazvaniya.md" in problem_messages(result)
    assert "title" in problem_messages(result)
    assert len(result.stages[0].modules[0].topics) == 2  # сломанная тема не загружена


def test_broken_yaml_reports_line_number(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "03-plohoy-yaml.md"
    write_file(path, "---\ntitle: Тема\nconcepts: [не закрыта\n---\nТекст\n")

    messages = problem_messages(load_content(content_dir))

    assert "Ошибка в YAML" in messages
    assert "строка" in messages


def test_missing_front_matter_is_reported(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "03-bez-shapki.md"
    write_file(path, "Просто текст без шапки\n")

    assert "должен начинаться со строки «---»" in problem_messages(load_content(content_dir))


def test_bad_file_name_is_reported(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "Моя тема.md"
    write_file(path, SIMPLE_TOPIC.format(title="Тема"))

    assert "Имя должно состоять из номера" in problem_messages(load_content(content_dir))


def test_duplicate_topic_name_is_reported(content_dir: Path):
    # Тема «terminal» уже есть в модуле linux — создаём вторую в модуле python.
    path = content_dir / "01-fundament" / "01-python" / "03-terminal.md"
    write_file(path, SIMPLE_TOPIC.format(title="Дубль"))

    result = load_content(content_dir)

    assert "уже используется" in problem_messages(result)
    all_slugs = [t.slug for m in result.stages[0].modules for t in m.topics]
    assert all_slugs.count("terminal") == 1


def test_unknown_field_is_reported_but_topic_is_loaded(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "03-opechatka.md"
    write_file(path, "---\ntitle: Тема\ngoall: опечатка в названии поля\n---\nТекст\n")

    result = load_content(content_dir)

    assert "Неизвестные поля: goall" in problem_messages(result)
    assert result.stages[0].modules[0].topics[-1].slug == "opechatka"


def test_bad_link_is_reported(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "03-ssylka.md"
    write_file(path, "---\ntitle: Тема\nlinks:\n  - title: Без адреса\n---\nТекст\n")

    assert "Ссылка №1" in problem_messages(load_content(content_dir))


def test_module_without_yaml_is_reported(content_dir: Path):
    (content_dir / "01-fundament" / "03-pusto").mkdir()

    assert "module.yaml" in problem_messages(load_content(content_dir))


def test_missing_content_folder_is_reported(tmp_path: Path):
    result = load_content(tmp_path / "нет-такой-папки")

    assert result.stages == []
    assert "не найдена" in problem_messages(result)


def test_real_content_folder_has_no_problems():
    """Материалы, которые лежат в репозитории, должны читаться без замечаний."""
    result = load_content(BASE_DIR / "content")

    assert result.problems == [], problem_messages(result)


# --- Квизы и карточки -----------------------------------------------------------


def test_reads_quiz_and_cards_next_to_topic(content_dir: Path):
    topic = load_content(content_dir).stages[0].modules[0].topics[0]

    assert len(topic.questions) == 2
    first = topic.questions[0]
    assert first.text == "Что выведет print(7 // 2)?"
    # Числа из YAML превращаются в текст, а «answer: 1» — в индекс 0.
    assert first.options == ["3", "3.5", "4"]
    assert first.correct_index == 0
    assert first.explanation == "Оператор // отбрасывает дробную часть."

    assert [card.front for card in topic.cards][0] == "Что делает оператор //?"
    assert len(topic.cards) == 3


def test_topic_without_quiz_files_has_empty_lists(content_dir: Path):
    topic = load_content(content_dir).stages[0].modules[0].topics[1]

    assert topic.questions == []
    assert topic.cards == []


def test_bad_question_is_skipped_but_others_are_kept(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "01-peremennye.quiz.yaml"
    write_file(
        path,
        "- question: Хороший вопрос?\n  options: [да, нет]\n  answer: 1\n"
        "- question: Номер ответа за пределами списка\n  options: [а, б]\n  answer: 5\n"
        "- question: Один вариант\n  options: [а]\n  answer: 1\n",
    )

    result = load_content(content_dir)
    topic = result.stages[0].modules[0].topics[0]

    assert [question.text for question in topic.questions] == ["Хороший вопрос?"]
    messages = problem_messages(result)
    assert "Элемент №2" in messages and "число от 1 до 2" in messages
    assert "Элемент №3" in messages and "от 2 до 6 вариантов" in messages


def test_yes_no_options_must_be_quoted(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "01-peremennye.quiz.yaml"
    # Без кавычек YAML читает yes и no как «истину» и «ложь», а не как слова.
    write_file(path, "- question: Вопрос?\n  options: [yes, no]\n  answer: 1\n")

    assert "возьми значение в кавычки" in problem_messages(load_content(content_dir))


def test_broken_quiz_file_does_not_hide_topic(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "01-peremennye.quiz.yaml"
    write_file(path, "- question: [не закрыта\n")

    result = load_content(content_dir)

    assert "01-peremennye.quiz.yaml" in problem_messages(result)
    assert result.stages[0].modules[0].topics[0].title == "Переменные"


def test_duplicate_card_is_reported(content_dir: Path):
    path = content_dir / "01-fundament" / "01-python" / "01-peremennye.cards.yaml"
    write_file(path, "- front: Вопрос?\n  back: Раз\n- front: вопрос?\n  back: Два\n")

    result = load_content(content_dir)

    assert "встречается дважды" in problem_messages(result)
    assert len(result.stages[0].modules[0].topics[0].cards) == 1
