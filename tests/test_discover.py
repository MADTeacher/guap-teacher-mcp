"""Offline tests for the HTML route-discovery helpers (no network)."""

from guap_teacher_mcp.discover import (
    extract_inside_links,
    extract_inside_links_labeled,
    normalize_pattern,
    page_title,
)

PROFILE_HTML = """
<html>
  <head><title>Личный кабинет</title></head>
  <body>
    <h3 class="text-center">Иванов Иван Иванович</h3>
    <nav>
      <a href="/inside/student/tasks/">Задания</a>
      <a href="/inside/student/tasks/123">Задание 123</a>
      <a href="https://pro.guap.ru/inside/student/materials">Материалы</a>
      <a href="https://drive.google.com/file/x">Внешний файл</a>
      <a href="/news">Новости</a>
      <a href="/inside/profile/456#anchor">Преподаватель</a>
      <a href="/inside/student/tasks/?semester=26">Семестр</a>
    </nav>
  </body>
</html>
"""

TITLE_HTML = """
<html><body><h3 class="page__title">Проверка отчётов</h3></body></html>
"""


def test_normalize_pattern_collapses_ids() -> None:
    assert normalize_pattern("/inside/profile/123") == "/inside/profile/{id}"
    assert normalize_pattern("/inside/student/tasks/9/reports/77") == (
        "/inside/student/tasks/{id}/reports/{id}"
    )
    assert normalize_pattern("/inside/profile") == "/inside/profile"


def test_extract_inside_links_filters_and_dedupes() -> None:
    links = extract_inside_links(PROFILE_HTML)
    assert links == {
        "/inside/student/tasks",  # query stripped, merged with the plain one
        "/inside/student/tasks/123",
        "/inside/student/materials",
        "/inside/profile/456",
    }


def test_extract_inside_links_labeled_keeps_texts() -> None:
    labeled = extract_inside_links_labeled(PROFILE_HTML)
    by_path = {item["path"]: item["text"] for item in labeled}
    assert by_path["/inside/student/tasks"] == "Задания"
    assert by_path["/inside/profile/456"] == "Преподаватель"
    assert "/news" not in by_path
    assert all(not path.startswith("http") for path in by_path)


def test_page_title_prefers_page_title_class() -> None:
    assert page_title(TITLE_HTML) == "Проверка отчётов"
    assert page_title(PROFILE_HTML) == "Личный кабинет"  # falls back to <title>
