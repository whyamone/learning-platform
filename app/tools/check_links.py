"""Проверка ссылок в учебных материалах.

Запуск:  make check-links
(или напрямую:  python -m app.tools.check_links)

Скрипт собирает все ссылки из папки content/, обращается к каждой
и печатает те, что не открываются. Нужен интернет.
"""

import sys
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.services.content_loader import load_content

TIMEOUT_SECONDS = 15
# Некоторые сайты не отвечают программам без этого заголовка.
HEADERS = {"User-Agent": "Mozilla/5.0 (link checker)"}
# Коды, при которых сайт жив, но не пускает автоматическую проверку:
# 401/403 — доступ запрещён, 429 — слишком много запросов.
BLOCKED_CODES = {401, 403, 429}


@dataclass
class LinkResult:
    url: str
    status: str  # "ok", "blocked" или "broken"
    detail: str = ""


def collect_links(content_dir: Path) -> dict[str, list[str]]:
    """Собрать ссылки из материалов: {адрес: [файлы тем, где он встречается]}."""
    links: dict[str, list[str]] = defaultdict(list)
    for stage in load_content(content_dir).stages:
        for module in stage.modules:
            for topic in module.topics:
                for link in topic.links:
                    links[link.url].append(topic.source_path)
    return dict(links)


def check_url(url: str) -> LinkResult:
    """Открыть адрес и определить, работает ли ссылка."""
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        # urlopen сам переходит по перенаправлениям (коды 301 и 302).
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return LinkResult(url, "ok", str(response.status))
    except urllib.error.HTTPError as error:
        # Сервер ответил, но кодом ошибки.
        if error.code in BLOCKED_CODES:
            return LinkResult(url, "blocked", f"код {error.code}")
        return LinkResult(url, "broken", f"код {error.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        # Сервер не ответил вообще: нет сети, неверное имя сайта, истекло время.
        return LinkResult(url, "broken", str(getattr(error, "reason", error)))


def main() -> int:
    links = collect_links(get_settings().content_dir)
    print(f"Проверяю ссылок: {len(links)}. Это займёт до минуты…")

    # Проверяем по восемь ссылок одновременно — так намного быстрее, чем по одной.
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check_url, links))

    broken = [result for result in results if result.status == "broken"]
    blocked = [result for result in results if result.status == "blocked"]

    for title, group in (
        ("Не открываются", broken),
        ("Сайт не пускает автоматическую проверку — открой в браузере", blocked),
    ):
        if not group:
            continue
        print(f"\n{title}:")
        for result in group:
            print(f"  {result.url}  ({result.detail})")
            for source_path in links[result.url]:
                print(f"      content/{source_path}")

    ok_count = len(results) - len(broken) - len(blocked)
    print(
        f"\nИтого: работает {ok_count}, не открывается {len(broken)}, не проверено {len(blocked)}."
    )
    # Код возврата 1 сообщает оболочке и make, что найдены проблемы.
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
