"""ИИ-наставник: разговор с локальной языковой моделью по теме.

Модель работает в Ollama на твоём компьютере. Мы обращаемся к ней по
OpenAI-совместимому API: это один POST-запрос на адрес /chat/completions
со списком сообщений. Тот же код заработает с любым другим сервером,
который понимает этот формат, — достаточно сменить адрес в настройках.

Файл состоит из трёх частей:

1. build_messages — собирает список сообщений для модели (чистая функция);
2. ask_model      — отправляет запрос и возвращает текст ответа;
3. функции для хранения истории разговора в базе.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import MentorMessage, Topic

# Модель видит ограниченный объём текста (контекстное окно), и у локальных
# моделей он небольшой. Поэтому теорию обрезаем, а из истории берём только конец.
MAX_THEORY_CHARS = 3500
MAX_PRACTICE_CHARS = 1500
MAX_HISTORY_MESSAGES = 8
MAX_USER_MESSAGE_CHARS = 6000


class MentorError(Exception):
    """Не удалось получить ответ модели. Текст показывается пользователю."""


class MentorMode(StrEnum):
    """Три режима наставника. От режима зависит инструкция для модели."""

    EXPLAIN = "explain"
    REVIEW = "review"
    INTERVIEW = "interview"

    @property
    def label(self) -> str:
        return _MODES[self].label

    @property
    def placeholder(self) -> str:
        """Подсказка в поле ввода."""
        return _MODES[self].placeholder

    @property
    def starter(self) -> str:
        """Готовое первое сообщение — для кнопки быстрого старта."""
        return _MODES[self].starter


@dataclass(frozen=True)
class _ModeInfo:
    label: str
    placeholder: str
    starter: str
    instruction: str


_MODES = {
    MentorMode.EXPLAIN: _ModeInfo(
        label="Объясни проще",
        placeholder="Что именно непонятно? Например: «не понимаю, зачем нужен return»",
        starter="Объясни главную мысль этой темы простыми словами, с примером из жизни.",
        instruction=(
            "Режим «Объясни проще». Объясняй так, как объяснял бы человеку, который "
            "программирует первые недели: короткими предложениями, без жаргона, "
            "с аналогией из жизни или из сетевых технологий и с маленьким примером кода. "
            "Каждый новый термин сразу поясняй. В конце задай один вопрос, "
            "чтобы проверить, что объяснение понято."
        ),
    ),
    MentorMode.REVIEW: _ModeInfo(
        label="Проверь моё решение",
        placeholder="Вставь сюда код решения и напиши, какое задание решал",
        starter="Как лучше прислать решение на проверку и на что ты будешь смотреть?",
        instruction=(
            "Режим «Проверь моё решение». Ученик присылает код. Сначала скажи, "
            "что сделано хорошо. Затем укажи ошибки и объясни, почему это ошибки. "
            "Не переписывай решение целиком: дай подсказку и покажи только проблемное "
            "место, чтобы ученик исправил сам. Если кода в сообщении нет, попроси его прислать."
        ),
    ),
    MentorMode.INTERVIEW: _ModeInfo(
        label="Спроси меня как на собеседовании",
        placeholder="Напиши ответ на вопрос наставника",
        starter="Задай мне первый вопрос по этой теме.",
        instruction=(
            "Режим «Собеседование». Ты — доброжелательный интервьюер на позицию "
            "junior-разработчика. Задавай по одному вопросу по теме, от простых к сложным. "
            "После ответа ученика коротко оцени его: что верно, что упущено, "
            "как ответить лучше. Затем задай следующий вопрос. Сам на свои вопросы "
            "заранее не отвечай."
        ),
    ),
}

BASE_INSTRUCTION = (
    "Ты — наставник на учебной платформе. Твой ученик — сетевой инженер, который "
    "с нуля учится на разработчика LLM-приложений на Python. Отвечай по-русски, "
    "кратко и по делу. Английские термины поясняй. Код оформляй блоками Markdown. "
    "Если чего-то не знаешь или вопрос выходит за рамки темы, честно скажи об этом. "
    "Ниже между метками приведены материалы темы — опирайся на них."
)


def _cut(text: str, limit: int) -> str:
    """Обрезать слишком длинный текст и пометить это."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n[…текст сокращён…]"


def build_system_prompt(topic: Topic, mode: MentorMode) -> str:
    """Собрать системную инструкцию: роль, режим и материалы темы."""
    parts = [BASE_INSTRUCTION, _MODES[mode].instruction, "<тема>", f"Название: {topic.title}"]
    if topic.goal:
        parts.append(f"Цель: {topic.goal}")
    if topic.concepts:
        parts.append("Ключевые понятия: " + "; ".join(topic.concepts))
    if topic.theory_md:
        parts.append("Теория:\n" + _cut(topic.theory_md, MAX_THEORY_CHARS))
    if topic.practice_md:
        parts.append("Практические задания:\n" + _cut(topic.practice_md, MAX_PRACTICE_CHARS))
    parts.append("</тема>")
    return "\n\n".join(parts)


def build_messages(
    topic: Topic, mode: MentorMode, history: Sequence[MentorMessage], user_text: str
) -> list[dict[str, str]]:
    """Собрать список сообщений для модели.

    Модель ничего не помнит между запросами, поэтому каждый раз получает
    всё заново: инструкцию, последние реплики разговора и новый вопрос.
    """
    messages = [{"role": "system", "content": build_system_prompt(topic, mode)}]
    for message in history[-MAX_HISTORY_MESSAGES:]:
        messages.append({"role": message.role, "content": message.content})
    messages.append({"role": "user", "content": user_text})
    return messages


def clean_reply(text: str) -> str:
    """Убрать из ответа служебные размышления модели.

    Некоторые модели сначала «думают вслух» внутри тегов <think>…</think>.
    Ученику это показывать незачем.
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def ask_model(
    base_url: str, model: str, messages: list[dict[str, str]], timeout_seconds: float
) -> str:
    """Отправить запрос серверу модели и вернуть текст ответа."""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": model, "messages": messages, "stream": False, "temperature": 0.4}

    try:
        response = httpx.post(url, json=payload, timeout=timeout_seconds)
    except httpx.TimeoutException:
        raise MentorError(
            "Модель не ответила за отведённое время. Первый запрос после запуска бывает "
            "долгим — попробуй ещё раз. Если повторяется, выбери модель поменьше."
        ) from None
    except httpx.HTTPError:
        # Сюда попадает и «соединение отклонено», и «имя узла не найдено».
        raise MentorError(
            f"Не удалось подключиться к серверу модели по адресу {base_url}. "
            "Проверь, что Ollama запущена."
        ) from None

    if response.status_code == 404:
        raise MentorError(f"Модель «{model}» не найдена. Скачай её командой: ollama pull {model}")
    if response.status_code >= 400:
        raise MentorError(f"Сервер модели ответил ошибкой {response.status_code}.")

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise MentorError("Сервер модели вернул ответ в непонятном формате.") from None

    reply = clean_reply(str(content or ""))
    if not reply:
        raise MentorError("Модель вернула пустой ответ. Попробуй переформулировать вопрос.")
    return reply


# --- История разговора ----------------------------------------------------------


def get_history(db: Session, topic: Topic, mode: MentorMode) -> list[MentorMessage]:
    """Все сообщения разговора по теме в заданном режиме, по порядку."""
    query = (
        select(MentorMessage)
        .where(MentorMessage.topic_id == topic.id, MentorMessage.mode == mode.value)
        .order_by(MentorMessage.id)
    )
    return list(db.scalars(query))


def validate_user_text(text: str) -> str:
    text = text.strip()
    if not text:
        raise MentorError("Напиши сообщение для наставника.")
    if len(text) > MAX_USER_MESSAGE_CHARS:
        raise MentorError(f"Сообщение длиннее {MAX_USER_MESSAGE_CHARS} символов — сократи его.")
    return text


def save_exchange(db: Session, topic: Topic, mode: MentorMode, user_text: str, reply: str) -> None:
    """Сохранить вопрос и ответ. Вызывается только после успешного ответа модели,
    чтобы в истории не оставалось вопросов без ответа."""
    db.add(MentorMessage(topic=topic, mode=mode.value, role="user", content=user_text))
    db.add(MentorMessage(topic=topic, mode=mode.value, role="assistant", content=reply))
    db.commit()


def clear_history(db: Session, topic: Topic, mode: MentorMode) -> None:
    """Начать разговор заново."""
    db.execute(
        delete(MentorMessage).where(
            MentorMessage.topic_id == topic.id, MentorMessage.mode == mode.value
        )
    )
    db.commit()
