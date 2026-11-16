"""Тесты ИИ-наставника.

Настоящая модель в тестах не нужна: функция httpx.post подменяется
заготовкой, которая возвращает заранее подготовленный ответ.
"""

from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.main import create_app
from app.services import mentor as mentor_service
from app.services import roadmap as roadmap_service
from app.services.importer import import_content
from app.services.mentor import MentorError, MentorMode


def fake_response(status_code: int = 200, content: str = "Ответ модели", json_data=None):
    """Ответ сервера модели в формате OpenAI."""
    if json_data is None:
        json_data = {"choices": [{"message": {"role": "assistant", "content": content}}]}
    return httpx.Response(status_code, json=json_data, request=httpx.Request("POST", "http://x"))


@pytest.fixture
def sent(monkeypatch) -> list[dict]:
    """Подменить httpx.post и запоминать, что было отправлено модели."""
    calls: list[dict] = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return fake_response(content="**Переменная** — это имя для значения.")

    monkeypatch.setattr(mentor_service.httpx, "post", fake_post)
    return calls


@pytest.fixture
def topic(db_session: Session, content_dir: Path):
    import_content(db_session, content_dir)
    return roadmap_service.get_topic(db_session, "peremennye")


@pytest.fixture
def mentor_client(db_session: Session, content_dir: Path) -> Iterator[TestClient]:
    """Приложение с включённым наставником."""
    import_content(db_session, content_dir)
    application = create_app(import_on_startup=False)
    application.dependency_overrides[get_db] = lambda: db_session
    application.dependency_overrides[get_settings] = lambda: Settings(
        content_dir=content_dir, ai_mentor_enabled=True, ollama_model="test-model"
    )
    with TestClient(application) as test_client:
        yield test_client


# --- Сборка запроса ----------------------------------------------------------------


def test_system_prompt_contains_topic_and_mode(topic):
    prompt = mentor_service.build_system_prompt(topic, MentorMode.INTERVIEW)

    assert "Название: Переменные" in prompt
    assert "Цель: Научиться создавать переменные." in prompt
    assert "переменная; присваивание" in prompt
    assert "Переменная — это **имя** для значения." in prompt  # теория темы
    assert "Создай переменную" in prompt  # практика
    assert "Собеседование" in prompt
    assert "Объясни проще" not in prompt


def test_long_theory_is_cut(topic):
    topic.theory_md = "А" * 10_000

    prompt = mentor_service.build_system_prompt(topic, MentorMode.EXPLAIN)

    assert "[…текст сокращён…]" in prompt
    assert len(prompt) < 7_000


def test_messages_include_recent_history_only(db_session: Session, topic):
    for number in range(10):
        mentor_service.save_exchange(
            db_session, topic, MentorMode.EXPLAIN, f"вопрос {number}", f"ответ {number}"
        )
    history = mentor_service.get_history(db_session, topic, MentorMode.EXPLAIN)

    messages = mentor_service.build_messages(topic, MentorMode.EXPLAIN, history, "новый вопрос")

    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "новый вопрос"}
    assert len(messages) == 1 + mentor_service.MAX_HISTORY_MESSAGES + 1
    assert messages[1]["content"] == "вопрос 6"  # старые реплики отброшены


def test_history_is_separate_for_each_mode(db_session: Session, topic):
    mentor_service.save_exchange(db_session, topic, MentorMode.EXPLAIN, "в1", "о1")

    assert len(mentor_service.get_history(db_session, topic, MentorMode.EXPLAIN)) == 2
    assert mentor_service.get_history(db_session, topic, MentorMode.REVIEW) == []


# --- Запрос к модели ---------------------------------------------------------------


def test_ask_model_sends_openai_style_request(sent):
    reply = mentor_service.ask_model(
        "http://ollama:11434/v1/", "qwen", [{"role": "user", "content": "привет"}], 30
    )

    assert reply == "**Переменная** — это имя для значения."
    assert sent[0]["url"] == "http://ollama:11434/v1/chat/completions"
    assert sent[0]["json"]["model"] == "qwen"
    assert sent[0]["json"]["stream"] is False
    assert sent[0]["timeout"] == 30


def test_thinking_block_is_removed():
    text = "<think>Сначала подумаю…\nещё подумаю</think>\n\nГотовый ответ."

    assert mentor_service.clean_reply(text) == "Готовый ответ."


def ask(monkeypatch, result):
    """Вызвать ask_model, заставив httpx.post вернуть `result` или выбросить его."""

    def fake_post(url, json, timeout):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(mentor_service.httpx, "post", fake_post)
    return mentor_service.ask_model("http://x/v1", "qwen", [], 5)


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (httpx.ConnectError("refused"), "Проверь, что Ollama запущена"),
        (httpx.ReadTimeout("slow"), "не ответила за отведённое время"),
        (fake_response(404), "ollama pull qwen"),
        (fake_response(500), "ответил ошибкой 500"),
        (fake_response(json_data={"unexpected": True}), "непонятном формате"),
        (fake_response(content="<think>только мысли</think>"), "пустой ответ"),
    ],
)
def test_model_failures_become_readable_errors(monkeypatch, result, expected):
    with pytest.raises(MentorError, match=expected):
        ask(monkeypatch, result)


def test_user_text_is_validated():
    with pytest.raises(MentorError):
        mentor_service.validate_user_text("   ")
    with pytest.raises(MentorError):
        mentor_service.validate_user_text("я" * 7000)
    assert mentor_service.validate_user_text("  вопрос  ") == "вопрос"


# --- Страницы ----------------------------------------------------------------------


def test_mentor_is_hidden_and_closed_when_disabled(client):
    assert "ИИ-наставник" not in client.get("/topics/peremennye").text
    assert client.get("/topics/peremennye/mentor").status_code == 404
    response = client.post("/topics/peremennye/mentor", data={"mode": "explain", "text": "?"})
    assert response.status_code == 404


def test_topic_page_shows_mentor_when_enabled(mentor_client):
    html = mentor_client.get("/topics/peremennye").text

    assert "ИИ-наставник" in html
    assert "test-model" in html
    for label in ("Объясни проще", "Проверь моё решение", "Спроси меня как на собеседовании"):
        assert label in html
    assert "Разговор ещё не начат" in html


def test_chat_round_trip(mentor_client, sent):
    response = mentor_client.post(
        "/topics/peremennye/mentor",
        data={"mode": "explain", "text": "Что такое переменная?"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "<html" not in response.text
    assert "Что такое переменная?" in response.text
    assert "<strong>Переменная</strong>" in response.text  # ответ отрисован как Markdown
    # Модели ушли инструкция с материалами темы и вопрос.
    messages = sent[0]["json"]["messages"]
    assert "Название: Переменные" in messages[0]["content"]
    assert messages[-1]["content"] == "Что такое переменная?"
    # Разговор сохранился и виден при следующем открытии темы.
    assert "Что такое переменная?" in mentor_client.get("/topics/peremennye").text


def test_second_message_carries_history(mentor_client, sent):
    for text in ("Первый вопрос", "Второй вопрос"):
        mentor_client.post("/topics/peremennye/mentor", data={"mode": "explain", "text": text})

    roles = [message["role"] for message in sent[1]["json"]["messages"]]
    assert roles == ["system", "user", "assistant", "user"]


def test_starter_button_sends_ready_text(mentor_client, sent):
    # Браузер отправляет и пустое поле, и значение нажатой кнопки — побеждает кнопка.
    mentor_client.post(
        "/topics/peremennye/mentor",
        data={"mode": "interview", "text": ["", MentorMode.INTERVIEW.starter]},
    )

    assert sent[0]["json"]["messages"][-1]["content"] == MentorMode.INTERVIEW.starter
    assert "Собеседование" in sent[0]["json"]["messages"][0]["content"]


def test_model_error_is_shown_and_text_is_kept(mentor_client, monkeypatch):
    def refuse(url, json, timeout):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(mentor_service.httpx, "post", refuse)

    response = mentor_client.post(
        "/topics/peremennye/mentor",
        data={"mode": "review", "text": "print('мой код')"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "Проверь, что Ollama запущена" in response.text
    assert "print(&#39;мой код&#39;)" in response.text  # текст вернулся в поле ввода
    assert "Разговор ещё не начат" in response.text  # в историю ничего не попало


def test_modes_switch_and_history_can_be_cleared(mentor_client, sent):
    mentor_client.post("/topics/peremennye/mentor", data={"mode": "explain", "text": "Вопрос"})

    other = mentor_client.get("/topics/peremennye/mentor?mode=review").text
    assert "Разговор ещё не начат" in other
    assert "Вставь сюда код решения" in other

    cleared = mentor_client.post(
        "/topics/peremennye/mentor/clear", data={"mode": "explain"}, headers={"HX-Request": "true"}
    )
    assert "Разговор ещё не начат" in cleared.text


def test_model_output_cannot_inject_html(mentor_client, monkeypatch):
    monkeypatch.setattr(
        mentor_service.httpx,
        "post",
        lambda url, json, timeout: fake_response(content="<script>alert(1)</script>"),
    )

    response = mentor_client.post(
        "/topics/peremennye/mentor",
        data={"mode": "explain", "text": "?"},
        headers={"HX-Request": "true"},
    )

    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text
