"""Тесты резервного копирования базы."""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from app.tools import backup


def make_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE notes (text TEXT)")
    connection.execute("INSERT INTO notes VALUES ('важная запись')")
    connection.commit()
    connection.close()


def test_backup_is_a_working_copy(tmp_path: Path):
    source = tmp_path / "app.db"
    make_database(source)

    target = backup.make_backup(source, tmp_path / "backups", datetime(2026, 3, 4, 18, 30, 5))

    assert target.name == "app-2026-03-04-183005.db"
    copy = sqlite3.connect(target)
    assert copy.execute("SELECT text FROM notes").fetchone() == ("важная запись",)
    copy.close()


def test_backup_without_database_fails_clearly(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        backup.make_backup(tmp_path / "нет.db", tmp_path / "backups", datetime.now())


def test_only_recent_backups_are_kept(tmp_path: Path):
    for day in range(1, 6):
        (tmp_path / f"app-2026-03-0{day}-120000.db").write_text("x")

    removed = backup.remove_old_backups(tmp_path, keep=2)

    assert [path.name for path in removed] == [
        "app-2026-03-01-120000.db",
        "app-2026-03-02-120000.db",
        "app-2026-03-03-120000.db",
    ]
    assert len(list(tmp_path.glob("app-*.db"))) == 2


def test_database_path_from_url():
    assert backup.database_path("sqlite:////app/data/app.db") == Path("/app/data/app.db")
    with pytest.raises(ValueError):
        backup.database_path("postgresql://server/db")
