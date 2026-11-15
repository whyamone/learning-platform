"""Превращение Markdown в HTML с подсветкой кода.

Markdown — простой способ размечать текст: `# заголовок`, `**жирный**`,
блоки кода в тройных обратных кавычках. Браузер его не понимает,
поэтому перед показом текст переводится в HTML.
"""

from markdown_it import MarkdownIt
from markupsafe import Markup, escape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

# nowrap=True: Pygments вернёт только раскрашенный код, без своей обёртки —
# обёртку <pre><code> мы добавляем сами ниже.
_formatter = HtmlFormatter(nowrap=True)


def _highlight_code(code: str, language: str, _attrs: str) -> str:
    """Раскрасить блок кода. Вызывается библиотекой для каждого блока ```...```."""
    try:
        # Лексер — часть Pygments, которая знает синтаксис конкретного языка.
        lexer = get_lexer_by_name(language)
        highlighted = highlight(code, lexer, _formatter)
    except ClassNotFound:
        # Язык не указан или неизвестен — показываем код как есть, но безопасно:
        # escape заменяет символы вроде «<», чтобы браузер не принял их за теги.
        highlighted = str(escape(code))

    return f'<pre class="highlight"><code>{highlighted}</code></pre>\n'


# Настроенный преобразователь. Создаётся один раз при запуске.
#   "commonmark" — стандартный диалект Markdown;
#   html=False   — HTML-теги в тексте не выполняются, а показываются как текст
#                  (это защита: на этапе с ИИ-наставником текст будет приходить от модели);
#   enable("table") — включить таблицы.
_markdown = MarkdownIt("commonmark", {"html": False, "highlight": _highlight_code}).enable("table")


def render_markdown(text: str) -> Markup:
    """Перевести Markdown в HTML.

    Возвращаем Markup — пометку «этот HTML безопасен». Без неё шаблон
    показал бы теги как обычный текст: `&lt;p&gt;` вместо абзаца.
    """
    return Markup(_markdown.render(text or ""))
