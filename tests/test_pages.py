"""Тесты страниц сайта."""

import re


def test_home_page_opens(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Платформа запущена" in response.text
    assert '<html lang="ru">' in response.text


def test_status_partial_shows_database_state(client):
    response = client.get("/partials/status")

    assert response.status_code == 200
    assert "подключена" in response.text
    # Это фрагмент, а не целая страница — тега <html> быть не должно.
    assert "<html" not in response.text


def test_static_files_are_served(client):
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/htmx.min.js").status_code == 200


def test_pages_do_not_load_anything_from_the_internet(client):
    """Приложение должно работать без интернета: никаких внешних адресов."""
    html = client.get("/").text

    # Ищем все значения src="..." и href="..." на странице.
    links = re.findall(r'(?:src|href)="([^"]+)"', html)

    assert links, "на странице должны быть ссылки на стили и скрипты"
    for link in links:
        assert not link.startswith(("http://", "https://", "//")) or "testserver" in link, link
