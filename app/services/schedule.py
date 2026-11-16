"""Расписание занятий: сколько минут ты готов учиться в каждый день недели.

Расписание хранится в таблице settings одной строкой в формате JSON
и меняется на странице «План». Пока ты его не менял, действует расписание
по умолчанию.
"""

import json

from sqlalchemy.orm import Session

from app.models import Setting

SETTING_KEY = "schedule"
MAX_MINUTES_PER_DAY = 12 * 60

# Дни недели нумеруются как в Python: 0 — понедельник, 6 — воскресенье.
# Пн, Ср, Чт — по 2 часа; Сб — 3,5 часа; Вс — 2 часа; Вт и Пт — без занятий.
DEFAULT_SCHEDULE: dict[int, int] = {0: 120, 1: 0, 2: 120, 3: 120, 4: 0, 5: 210, 6: 120}


def get_schedule(db: Session) -> dict[int, int]:
    """Вернуть расписание: {номер дня недели: минуты}."""
    setting = db.get(Setting, SETTING_KEY)
    if setting is None:
        return dict(DEFAULT_SCHEDULE)

    try:
        stored = json.loads(setting.value)
        # В JSON ключи всегда строки, поэтому превращаем их обратно в числа.
        return {day: int(stored.get(str(day), 0)) for day in range(7)}
    except (ValueError, TypeError, AttributeError):
        # Запись повреждена — лучше расписание по умолчанию, чем падение страницы.
        return dict(DEFAULT_SCHEDULE)


def save_schedule(db: Session, hours_by_day: dict[int, float]) -> dict[int, int]:
    """Сохранить расписание, заданное в часах. Вернуть его в минутах."""
    schedule = {}
    for day in range(7):
        minutes = round(float(hours_by_day.get(day, 0)) * 60)
        # Отрицательное и слишком большое значение приводим к допустимым границам.
        schedule[day] = max(0, min(minutes, MAX_MINUTES_PER_DAY))

    setting = db.get(Setting, SETTING_KEY)
    if setting is None:
        setting = Setting(key=SETTING_KEY)
        db.add(setting)
    setting.value = json.dumps(schedule)
    db.commit()
    return schedule


def weekly_hours(schedule: dict[int, int]) -> float:
    """Сколько часов в неделю получается по расписанию."""
    return sum(schedule.values()) / 60
