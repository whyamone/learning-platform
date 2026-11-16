"""Настройки приложения.

Все значения можно переопределить в файле `.env` (см. `.env.example`)
или через переменные окружения. Имена в `.env` пишутся ЗАГЛАВНЫМИ буквами:
поле `database_url` читается из переменной `DATABASE_URL`.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта: папка на уровень выше, чем `app/`.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Список настроек с типами и значениями по умолчанию."""

    # Откуда читать настройки и что делать с неизвестными переменными.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Название, которое видно в шапке сайта.
    app_name: str = "Учебная платформа"

    # Адрес базы данных. Для SQLite это «sqlite:///» + путь к файлу.
    # По умолчанию — файл data/app.db внутри проекта.
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"

    # Папка с учебными материалами (Markdown + YAML).
    content_dir: Path = BASE_DIR / "content"

    # Часовой пояс — по нему определяется, какой сегодня день.
    # Список названий: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    timezone: str = "Europe/Moscow"

    # Сколько новых карточек показывать в день. Ограничение нужно, чтобы после
    # большой темы на тебя не свалилось тридцать незнакомых карточек разом.
    new_cards_per_day: int = 10


@lru_cache
def get_settings() -> Settings:
    """Вернуть настройки.

    Декоратор `lru_cache` запоминает результат: файл `.env` читается
    один раз, а не при каждом обращении.
    """
    return Settings()
