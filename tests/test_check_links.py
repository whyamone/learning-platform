"""Тесты программы проверки ссылок.

Настоящих запросов в интернет тесты не делают: функция urlopen
подменяется заготовкой, которая возвращает нужный нам результат.
"""

import urllib.error
from pathlib import Path

from app.tools import check_links


class FakeResponse:
    """Заменитель ответа сервера с кодом 200."""

    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_collect_links_groups_topics_by_url(content_dir: Path):
    links = check_links.collect_links(content_dir)

    assert links == {
        "https://docs.python.org/3/tutorial/": ["01-fundament/01-python/01-peremennye.md"]
    }


def test_working_link_is_ok(monkeypatch):
    monkeypatch.setattr(check_links.urllib.request, "urlopen", lambda *a, **k: FakeResponse())

    assert check_links.check_url("https://example.com/").status == "ok"


def test_missing_page_is_broken(monkeypatch):
    def raise_not_found(request, **_kwargs):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", None, None)

    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_not_found)

    result = check_links.check_url("https://example.com/missing")
    assert (result.status, result.detail) == ("broken", "код 404")


def test_forbidden_page_is_reported_separately(monkeypatch):
    def raise_forbidden(request, **_kwargs):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", None, None)

    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_forbidden)

    assert check_links.check_url("https://example.com/").status == "blocked"


def test_unreachable_site_is_broken(monkeypatch):
    def raise_no_network(*_args, **_kwargs):
        raise urllib.error.URLError("нет сети")

    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_no_network)

    result = check_links.check_url("https://no-such-site.example/")
    assert result.status == "broken"
    assert "нет сети" in result.detail
