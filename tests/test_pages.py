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
    pages = ("/", "/roadmap", "/topics/peremennye", "/topics/peremennye/quiz", "/review")
    for url in (*pages, "/time", "/journal"):
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


# --- Квизы -----------------------------------------------------------------------


def question_field_names(html: str) -> list[str]:
    """Имена групп переключателей на странице квиза, по порядку вопросов."""
    names = re.findall(r'name="(q-\d+)"', html)
    return list(dict.fromkeys(names))  # убрать повторы, сохранив порядок


def test_topic_page_offers_quiz_and_mentions_cards(client):
    html = client.get("/topics/peremennye").text

    assert "Проверь себя" in html
    assert "Пройти квиз" in html
    assert "Карточек для повторения: 3" in html


def test_quiz_page_shows_questions_without_answers(client):
    response = client.get("/topics/peremennye/quiz")

    assert response.status_code == 200
    assert "Что выведет print(7 // 2)?" in response.text
    assert len(question_field_names(response.text)) == 2
    # Объяснение нельзя показывать до ответа.
    assert "отбрасывает дробную часть" not in response.text


def test_topic_without_questions_has_no_quiz_page(client):
    assert client.get("/topics/usloviya/quiz").status_code == 404
    assert "Проверь себя" not in client.get("/topics/usloviya").text


def test_submit_quiz_shows_score_and_explanations(client):
    first, second = question_field_names(client.get("/topics/peremennye/quiz").text)

    # Первый ответ верный (вариант 0), второй — нет (нужен вариант 1).
    response = client.post("/topics/peremennye/quiz", data={first: "0", second: "0"})

    assert response.status_code == 200
    assert "1 из 2 · 50%" in response.text
    assert "отбрасывает дробную часть" in response.text
    assert "правильный ответ" in response.text
    assert "твой ответ" in response.text
    # Попытка сохранилась и видна на странице темы.
    assert "лучший результат: 50%" in client.get("/topics/peremennye").text


def test_submit_quiz_without_answers_counts_zero(client):
    response = client.post("/topics/peremennye/quiz", data={})

    assert "0 из 2 · 0%" in response.text
    assert "нет ответа" in response.text


def test_passed_quiz_suggests_marking_topic_done(client):
    first, second = question_field_names(client.get("/topics/peremennye/quiz").text)

    response = client.post("/topics/peremennye/quiz", data={first: "0", second: "1"})

    assert "2 из 2 · 100%" in response.text
    assert "Квиз пройден" in response.text


# --- Повторение карточек -----------------------------------------------------------


def start_topic(client, slug: str = "peremennye") -> None:
    client.post(f"/topics/{slug}/status", data={"status": "in_progress"})


def current_card_url(html: str) -> str:
    """Адрес, на который отправляется оценка текущей карточки."""
    return re.search(r'action="([^"]*/review/\d+)"', html).group(1)


def test_review_is_empty_until_topic_is_started(client):
    response = client.get("/review")

    assert response.status_code == 200
    assert "На сегодня всё" in response.text
    assert "На сегодня карточек нет" in client.get("/").text


def test_review_shows_card_after_topic_is_started(client):
    start_topic(client)

    html = client.get("/review").text

    assert "Осталось на сегодня: 3" in html
    assert "Что делает оператор //?" in html
    assert "новая карточка" in html
    assert "<strong>отбрасывает</strong>" in html  # оборот карточки — тоже Markdown
    for label in ("Не помню", "С трудом", "Хорошо", "Легко"):
        assert label in html
    assert "Карточек на сегодня: <strong>3</strong>" in client.get("/").text


def test_grading_card_with_htmx_returns_next_card(client):
    start_topic(client)
    url = current_card_url(client.get("/review").text)

    response = client.post(url, data={"grade": "good"}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "<html" not in response.text
    assert "Осталось на сегодня: 2" in response.text
    assert "Чем = отличается от ==?" in response.text


def test_grading_card_without_htmx_redirects(client):
    start_topic(client)
    url = current_card_url(client.get("/review").text)

    response = client.post(url, data={"grade": "easy"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].endswith("/review")


def test_review_finishes_when_all_cards_are_graded(client):
    start_topic(client)

    for _ in range(3):
        url = current_card_url(client.get("/review").text)
        client.post(url, data={"grade": "good"})

    assert "На сегодня всё" in client.get("/review").text


def test_grading_rejects_unknown_grade_and_unknown_card(client):
    start_topic(client)
    url = current_card_url(client.get("/review").text)

    assert client.post(url, data={"grade": "отлично"}).status_code == 422
    assert client.post("/review/999999", data={"grade": "good"}).status_code == 404


# --- Время, журнал, дашборд -------------------------------------------------------


def test_dashboard_shows_week_streak_and_forecast(client):
    html = client.get("/").text

    for text in ("Эта неделя", "Серия", "Темп", "Занятия по дням", "Этапы и прогноз"):
        assert text in html
    assert "0 дней" in html
    assert "плановый" in html  # занятий ещё нет — темп берётся из плана
    assert "примерно до" in html


def test_timer_start_and_stop_from_topic_page(client):
    assert "Начать занятие" in client.get("/topics/peremennye").text
    assert "Идёт занятие" not in client.get("/partials/timer").text

    response = client.post(
        "/timer/start", data={"topic_slug": "peremennye"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"].endswith("/topics/peremennye")

    timer = client.get("/partials/timer").text
    assert "Идёт занятие" in timer
    assert "Переменные" in timer

    stopped = client.post("/timer/stop", headers={"HX-Request": "true"})
    assert stopped.headers["HX-Refresh"] == "true"
    assert "Идёт занятие" not in client.get("/partials/timer").text


def test_manual_session_appears_in_list_and_on_dashboard(client):
    from app.timeutils import local_today

    today = local_today("Europe/Moscow").isoformat()
    response = client.post("/time", data={"day": today, "minutes": "90", "topic_slug": "terminal"})

    assert response.status_code == 200
    assert "Терминал" in response.text
    assert 'value="90"' in response.text
    dashboard = client.get("/").text
    assert "1 ч 30 мин" in dashboard
    assert "1 день" in dashboard  # серия началась


def test_manual_session_with_bad_minutes_shows_error(client):
    from app.timeutils import local_today

    today = local_today("Europe/Moscow").isoformat()
    response = client.post("/time", data={"day": today, "minutes": "0"})

    assert response.status_code == 400
    assert "Минут должно быть" in response.text


def test_session_can_be_edited_and_deleted(client):
    from app.timeutils import local_today

    today = local_today("Europe/Moscow").isoformat()
    html = client.post("/time", data={"day": today, "minutes": "90"}).text
    session_url = re.search(r'action="([^"]*/time/\d+)"', html).group(1)

    assert 'value="45"' in client.post(session_url, data={"minutes": "45"}).text
    assert "Занятий пока нет" in client.post(f"{session_url}/delete").text
    assert client.post("/time/999999/delete").status_code == 404


def test_journal_entry_on_topic_page_and_journal_page(client):
    response = client.post(
        "/topics/peremennye/journal",
        data={"text": "Решил **все** задачи", "url": "https://github.com/me/study"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "<html" not in response.text
    assert "<strong>все</strong>" in response.text
    assert "https://github.com/me/study" in response.text

    journal = client.get("/journal").text
    assert "Переменные" in journal
    assert "https://github.com/me/study" in journal


def test_journal_shows_error_and_keeps_text(client):
    response = client.post(
        "/topics/peremennye/journal",
        data={"text": "моя заметка", "url": "javascript:alert(1)"},
        headers={"HX-Request": "true"},
    )

    assert "Ссылка должна начинаться" in response.text
    assert "моя заметка" in response.text  # введённое не потерялось
    assert "Записей пока нет" in client.get("/journal").text


def test_journal_entry_can_be_deleted(client):
    client.post("/topics/peremennye/journal", data={"text": "черновик"})
    delete_url = re.search(r'action="([^"]*/journal/\d+/delete)"', client.get("/journal").text)

    response = client.post(delete_url.group(1))

    assert "Записей пока нет" in response.text
