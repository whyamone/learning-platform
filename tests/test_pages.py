"""Тесты страниц сайта."""

import re
from pathlib import Path

from tests.helpers import SIMPLE_TOPIC, write_file


def test_home_page_shows_next_topic(client):
    response = client.get("/")

    assert response.status_code == 200
    assert '<html lang="ru">' in response.text
    assert "Следующая тема" in response.text
    assert "Переменные" in response.text


def test_status_partial_shows_database_state(client):
    response = client.get("/partials/status")

    assert response.status_code == 200
    assert "подключена" in response.text
    # Это фрагмент, а не целая страница — тега <html> быть не должно.
    assert "<html" not in response.text


def test_static_files_are_served(client):
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/css/pygments.css").status_code == 200
    assert client.get("/static/js/htmx.min.js").status_code == 200


def test_pages_do_not_load_anything_from_the_internet(client):
    """Приложение должно работать без интернета: стили и скрипты — только свои."""
    for url in ("/", "/roadmap", "/topics/peremennye"):
        html = client.get(url).text

        # Адреса, которые браузер загружает сам: <script src>, <img src>, <link href>.
        # Обычные ссылки <a href> сюда не входят — их открывает человек по клику.
        resources = re.findall(r'<(?:script|img)[^>]*\ssrc="([^"]+)"', html)
        resources += re.findall(r'<link[^>]*\shref="([^"]+)"', html)

        assert resources, f"на странице {url} должны быть свои стили и скрипты"
        for resource in resources:
            assert resource.startswith("http://testserver/static/"), resource


def test_roadmap_shows_stages_modules_and_topics(client):
    response = client.get("/roadmap")

    assert response.status_code == 200
    for text in ("Фундамент", "месяцы 1–4", "Python", "Linux", "Переменные", "Терминал"):
        assert text in response.text
    assert "0 из 3 · 0%" in response.text
    assert "Замечания к материалам" not in response.text


def test_topic_page_shows_all_sections(client):
    response = client.get("/topics/peremennye")

    assert response.status_code == 200
    html = response.text
    for text in ("Цель", "Ключевые понятия", "Теория", "Словарик", "Практика", "Материалы"):
        assert text in html
    assert "<strong>имя</strong>" in html  # Markdown превратился в HTML
    assert '<pre class="highlight">' in html  # код подсвечен
    assert "https://docs.python.org/3/tutorial/" in html
    assert "на английском" in html
    assert "2,5 ч" in html
    assert "Условия" in html  # ссылка на следующую тему


def test_unknown_topic_gives_404(client):
    assert client.get("/topics/net-takoy-temy").status_code == 404


def test_change_status_with_htmx_returns_fragment(client):
    response = client.post(
        "/topics/peremennye/status",
        data={"status": "in_progress"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "<html" not in response.text
    assert re.search(r"status-btn-in_progress\s+is-current", response.text)
    # Статус сохранился: главная теперь предлагает «Продолжить».
    assert "Продолжить" in client.get("/").text


def test_change_status_without_htmx_redirects_to_topic(client):
    response = client.post(
        "/topics/peremennye/status", data={"status": "done"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/topics/peremennye")
    assert "1 из 3 · 33%" in client.get("/roadmap").text


def test_change_status_rejects_unknown_value(client):
    response = client.post("/topics/peremennye/status", data={"status": "выдуманный"})

    assert response.status_code == 422


def test_reimport_picks_up_new_topic_and_shows_problems(client, content_dir: Path):
    module = content_dir / "01-fundament" / "02-linux"
    write_file(module / "02-prava.md", SIMPLE_TOPIC.format(title="Права доступа"))
    write_file(module / "03-plohaya.md", "файл без шапки")

    response = client.post("/content/reimport")  # клиент сам переходит по редиректу

    assert response.status_code == 200
    assert "Права доступа" in response.text
    assert "Замечания к материалам (1)" in response.text
    assert "03-plohaya.md" in response.text
