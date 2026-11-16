"""Резервная копия базы данных.

Запуск:  make backup
(или напрямую:  python -m app.tools.backup)

Создаёт копию файла базы в папке data/backups/ с датой и временем в имени.
Копировать можно при работающем приложении: используется встроенный
в SQLite механизм резервного копирования, который даёт целую копию,
даже если в базу в этот момент что-то записывается.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import get_settings

# Сколько последних копий хранить. Более старые удаляются.
KEEP_BACKUPS = 10


def database_path(database_url: str) -> Path:
    """Достать путь к файлу из адреса вида sqlite:////app/data/app.db."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Резервная копия умеет работать только с базой SQLite.")
    return Path(database_url.removeprefix(prefix))


def make_backup(source: Path, backup_dir: Path, now: datetime) -> Path:
    """Скопировать базу в папку backup_dir и вернуть путь к копии."""
    if not source.exists():
        raise FileNotFoundError(f"Файл базы не найден: {source}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"app-{now:%Y-%m-%d-%H%M%S}.db"

    # Открываем обе базы и просим SQLite перенести содержимое.
    source_db = sqlite3.connect(source)
    target_db = sqlite3.connect(target)
    try:
        source_db.backup(target_db)
    finally:
        target_db.close()
        source_db.close()
    return target


def remove_old_backups(backup_dir: Path, keep: int = KEEP_BACKUPS) -> list[Path]:
    """Оставить `keep` самых свежих копий, остальные удалить. Вернуть удалённые."""
    # Имена содержат дату и время, поэтому сортировка по имени — это сортировка по времени.
    backups = sorted(backup_dir.glob("app-*.db"))
    old = backups[:-keep] if keep > 0 else backups
    for path in old:
        path.unlink()
    return old


def main() -> int:
    try:
        settings = get_settings()
        source = database_path(settings.database_url)
        backup_dir = source.parent / "backups"
        # Время в имени файла — местное, а не по часам контейнера (там UTC).
        now = datetime.now(ZoneInfo(settings.timezone))
        target = make_backup(source, backup_dir, now)
    except (ValueError, FileNotFoundError) as error:
        print(f"Не удалось создать копию: {error}")
        return 1

    removed = remove_old_backups(backup_dir)
    size_kb = target.stat().st_size / 1024
    print(f"Копия создана: data/backups/{target.name} ({size_kb:.0f} КБ)")
    if removed:
        print(f"Удалено старых копий: {len(removed)} (хранятся последние {KEEP_BACKUPS})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
