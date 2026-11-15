"""Тесты превращения Markdown в HTML."""

from app.services.markdown import render_markdown


def test_renders_basic_markdown():
    html = render_markdown("Это **важно**.")

    assert "<strong>важно</strong>" in html


def test_highlights_code_blocks():
    html = render_markdown('```python\nprint("привет")\n```')

    assert '<pre class="highlight">' in html
    # Pygments заворачивает части кода в <span class="...">, чтобы их раскрасить.
    assert "<span" in html


def test_code_block_with_unknown_language_is_shown_as_is():
    html = render_markdown("```неизвестный\n<b>код</b>\n```")

    assert "&lt;b&gt;код&lt;/b&gt;" in html


def test_html_tags_in_text_are_not_executed():
    html = render_markdown("<script>alert(1)</script>")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_renders_tables():
    html = render_markdown("| a | b |\n|---|---|\n| 1 | 2 |")

    assert "<table>" in html


def test_empty_text_gives_empty_result():
    assert render_markdown("") == ""
