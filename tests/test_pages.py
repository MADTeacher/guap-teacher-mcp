"""Offline tests for pages.py parsers (fixtures mirror real portal HTML)."""

from guap_teacher_mcp.pages import (
    parse_filter_options,
    parse_h5_card,
    parse_materials,
    parse_reports,
    parse_schedule,
    parse_subjects,
    parse_tasks,
)

REPORTS_HTML = """
<html><body>
<form action="/inside/professor/reports">
  <select name="semester"><option value="28" selected>2026/2027 осенний</option></select>
  <select name="status"><option value="0">Все</option><option value="1">ожидает проверки</option></select>
  <input name="token" value="csrf"/>
</form>
<table>
  <tr><th></th><th>Студент</th><th>Группа</th><th>Задание</th><th>Статус</th>
      <th>Комментарий студента</th><th>Комментарий преподавателя</th>
      <th>Предельная дата загрузки</th><th>Дата загрузки</th><th>Время проверки</th></tr>
  <tr>
    <td><a href="/inside/professor/reports/5658701/edit">Смотреть</a>
        <a href="/inside/professor/reports/5658701/download">Скачать</a></td>
    <td><a href="/inside/profile/53869">Брехова Екатерина Александровна</a></td>
    <td>4511з</td>
    <td><a href="/inside/professor/tasks/192715/show">ЛР 1</a></td>
    <td>ожидает проверки</td><td></td><td></td>
    <td>не задана</td><td>05.09.2026 18:18:16</td><td></td>
  </tr>
</table>
</body></html>
"""

TASKS_HTML = """
<html><body>
<form action="/inside/professor/tasks" method="get">
  <select name="semester"><option value="28" selected>2026/2027 осенний</option></select>
  <select name="subject"><option value="0">Все</option></select>
</form>
<table>
  <tr><th>Действия</th><th>№ в сем</th><th>Дисциплина</th><th>Название</th><th>Тип</th>
      <th>Предельная дата выполнения</th><th>Видимость студенту</th><th>Дата изменения</th></tr>
  <tr>
    <td><a href="/inside/professor/tasks/192715/show"></a>
        <a href="/inside/professor/tasks/28/192715/edit"></a></td>
    <td>1</td>
    <td><a href="/inside/subjects/3419299">Автоматизация проектирования интернет-приложений</a></td>
    <td><a href="/inside/professor/tasks/192715/show">ЛР</a></td>
    <td>Лабораторная работа</td><td>Не указана</td><td></td>
    <td>5-го октября 2026 в 23:00</td>
  </tr>
</table>
</body></html>
"""

MATERIALS_HTML = """
<html><body><table>
  <tr><th>Действия</th><th>Файл/Ссылка</th><th>Дисциплина</th><th>Название</th>
      <th>Группа</th><th>Видимость</th><th>Дата добавления</th></tr>
  <tr>
    <td><a href="/inside/professor/materials/28/113620/edit"></a>
        <a href="/inside/professor/materials/28/113620/copy"></a>
        <a href="/inside/professor/materials/113620/remove"></a></td>
    <td><a href="/storage/materials/123/file.pdf">file.pdf</a></td>
    <td><a href="/inside/subjects/3419390">Алгоритмы и структуры данных</a></td>
    <td>Учебные материалы</td><td>4514 4515</td><td>видим</td>
    <td>28.08.2026 12:44:20</td>
  </tr>
</table></body></html>
"""

SUBJECTS_HTML = """
<html><body>
<form action="/inside/subjects/new" method="get">
  <select name="semester">
    <option value="29">2026/2027 весенний</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
  <select name="group"><option value="0">Выбрать все</option><option value="7432">4514</option></select>
  <input name="searchtext" value=""/>
</form>
<a href="/inside/subjects/3419299">Автоматизация проектирования интернет-приложений</a>
<a href="/inside/subjects/3421988">Интернет-программирование</a>
<a href="/inside/subjects/get-unsatisfactory-marks/28">Cтатистика по должникам</a>
<a href="/inside/subjects/new">Дисциплины</a>
<ul class="pagination justify-content-center pagination-sm">
  <li class="page-item disabled"><span class="page-link">&laquo;&nbsp;Назад</span></li>
  <li class="page-item active"><span class="page-link">1</span></li>
  <li class="page-item"><a class="page-link" href="/inside/subjects/new?searchtext=&amp;semester=28&amp;page=2">2</a></li>
  <li class="page-item"><a class="page-link" rel="next" href="/inside/subjects/new?searchtext=&amp;semester=28&amp;page=2">Вперед&nbsp;&raquo;</a></li>
</ul>
</body></html>
"""

SUBJECTS_PAGE2_HTML = """
<html><body>
<ul class="pagination justify-content-center pagination-sm">
  <li class="page-item"><a class="page-link" href="/inside/subjects/new?searchtext=&amp;semester=28&amp;page=1">1</a></li>
  <li class="page-item active"><span class="page-link">2</span></li>
  <li class="page-item"><a class="page-link" href="/inside/subjects/new?searchtext=&amp;semester=28&amp;page=3">3</a></li>
  <li class="page-item disabled"><span class="page-link">Вперед</span></li>
</ul>
<a href="/inside/subjects/3423947">Распределенные информационные системы</a>
</body></html>
"""

CARD_HTML = """
<html><body>
<h3 class="page__title">Алгоритмы и структуры данных</h3>
<h5>Направление: 09.04.03 Прикладная информатика</h5>
<h5>Кафедра: Кафедра прикладной информатики (Кафедра 41)</h5>
<h5>Тип контроля: Экзамен</h5>
</body></html>
"""

SCHEDULE_WEEK_HTML = """
<html><body>
<select name="group"><option value="0">Все</option><option value="7432">4514</option></select>
<select name="teacher"><option value="0">Все</option><option value="40734">Парамонов К.В.</option></select>
<table>
  <tr><th>Пара</th><th>Время</th><th>Пн - 09.11</th><th>Вт - 10.11</th></tr>
  <tr><td>1</td><td>09:30 - 11:00</td>
      <td><a href="/inside/subjects/3419299">Интернет-программирование</a> ауд. 201</td><td></td></tr>
  <tr><td>2</td><td>11:10 - 12:40</td><td></td><td>Курсовая работа</td></tr>
</table></body></html>
"""


def test_parse_reports_extracts_row_and_filters() -> None:
    data = parse_reports(REPORTS_HTML)
    assert data["count"] == 1
    row = data["reports"][0]
    assert row["report_id"] == 5658701
    assert row["student"] == "Брехова Екатерина Александровна"
    assert row["student_id"] == 53869
    assert row["group"] == "4511з"
    assert row["task"] == "ЛР 1"
    assert row["status"] == "ожидает проверки"
    assert row["download_url"] == "/inside/professor/reports/5658701/download"
    opts = data["filter_options"]
    assert "semester" in opts and "status" in opts
    assert "token" not in opts


def test_parse_tasks_extracts_ids_and_links() -> None:
    data = parse_tasks(TASKS_HTML)
    assert data["count"] == 1
    row = data["tasks"][0]
    assert row["task_id"] == 192715
    assert row["subject_id"] == 3419299
    assert row["type"] == "Лабораторная работа"
    assert row["task_url"] == "/inside/professor/tasks/192715/show"
    assert row["deadline"] == "Не указана"


def test_parse_materials_extracts_file_url() -> None:
    data = parse_materials(MATERIALS_HTML)
    assert data["count"] == 1
    row = data["materials"][0]
    assert row["file_url"] == "/storage/materials/123/file.pdf"
    assert row["subject_id"] == 3419390
    assert row["groups"] == "4514 4515"


def test_parse_subjects_only_numeric_ids_and_default_semester() -> None:
    data = parse_subjects(SUBJECTS_HTML)
    assert data["count"] == 2
    assert {s["subject_id"] for s in data["subjects"]} == {3419299, 3421988}
    assert data["default_semester"] == "28"
    assert data["page"] == 1
    assert data["last_page"] == 2
    assert "searchtext" not in data["filter_options"]


def test_parse_subjects_pagination_active_and_last_page() -> None:
    data = parse_subjects(SUBJECTS_PAGE2_HTML)
    assert data["page"] == 2
    assert data["last_page"] == 3
    assert data["count"] == 1
    assert data["subjects"][0]["subject_id"] == 3423947


def test_parse_subjects_without_pagination_is_single_page() -> None:
    html = '<html><body><a href="/inside/subjects/3419299">Дисциплина</a></body></html>'
    data = parse_subjects(html)
    assert data["page"] == 1
    assert data["last_page"] == 1


def test_parse_h5_card() -> None:
    data = parse_h5_card(CARD_HTML)
    assert data["title"] == "Алгоритмы и структуры данных"
    assert data["fields"]["Тип контроля"] == "Экзамен"
    assert data["fields"]["Направление"].startswith("09.04.03")


def test_parse_schedule_week_cells_and_filters() -> None:
    data = parse_schedule(SCHEDULE_WEEK_HTML)
    assert data["headers"] == ["Пара", "Время", "Пн - 09.11", "Вт - 10.11"]
    assert len(data["rows"]) == 2
    monday = data["rows"][0]["days"][0]
    assert "Интернет-программирование" in monday["text"]
    assert "/inside/subjects/3419299" in monday["links"]
    assert data["rows"][1]["days"][1]["text"] == "Курсовая работа"
    assert "group" in data["filter_options"] and "teacher" in data["filter_options"]


def test_parse_filter_options_skips_service_selects() -> None:
    opts = parse_filter_options(REPORTS_HTML)
    assert set(opts) == {"semester", "status"}


REPORT_EDIT_HTML = """
<html><body>
<form action="/inside/professor/reports/5712788" method="POST">
  <input name="token" value="csrf-token-123"/>
  <input name="_method" value="PATCH"/>
  <input name="_referer_url" value=""/>
  <input name="uploadDatetime" value="2026-10-08 17:20:43"/>
  <textarea name="studentComment"></textarea>
  <select name="status">
    <option value="1" selected>ожидает проверки</option>
    <option value="2">принят</option>
    <option value="3">не принят</option>
  </select>
  <textarea name="profComment"></textarea>
  <input name="markPoint" value="0"/>
  <input name="taskId" value="191741"/>
  <input name="student" value="40750"/>
</form>
</body></html>
"""


def test_parse_report_review_form() -> None:
    from guap_teacher_mcp.pages import parse_report_review_form

    data = parse_report_review_form(REPORT_EDIT_HTML, 5712788)
    fields = data["fields"]
    assert fields["token"] == "csrf-token-123"
    assert fields["_method"] == "PATCH"
    assert fields["taskId"] == "191741"
    assert fields["student"] == "40750"
    assert fields["status"] == "1"
    assert data["status_options"] == [
        {"value": "1", "label": "ожидает проверки"},
        {"value": "2", "label": "принят"},
        {"value": "3", "label": "не принят"},
    ]


def test_parse_report_review_form_no_form() -> None:
    from guap_teacher_mcp.pages import parse_report_review_form

    data = parse_report_review_form("<html><body>нет формы</body></html>", 1)
    assert data == {"fields": {}, "status_options": []}


def test_resolve_report_status() -> None:
    from guap_teacher_mcp.pages import KNOWN_REPORT_STATUSES, resolve_report_status

    assert resolve_report_status("2") == {"value": "2", "label": "принят"}
    assert resolve_report_status("Принят") == {"value": "2", "label": "принят"}
    # Empty page options fall back to the known enum (real edit form has
    # no <option>s: status arrives as a plain field).
    assert resolve_report_status("принят", []) == {"value": "2", "label": "принят"}
    assert resolve_report_status("мусор") is None
    assert KNOWN_REPORT_STATUSES[0]["value"] == "1"


def test_resolve_report_mark() -> None:
    from guap_teacher_mcp.pages import resolve_report_mark

    # Explicit mark: stringified for the POST, not kept.
    assert resolve_report_mark(8, "3") == ("8", False)
    assert resolve_report_mark(0, "5") == ("0", False)
    # mark=None: the current form markPoint is re-sent unchanged, so only
    # the status/comment change.
    assert resolve_report_mark(None, "3") == ("3", True)
    # Kept mark with no markPoint field in the form: nothing to re-send.
    assert resolve_report_mark(None, None) == (None, True)


def test_validate_task_update() -> None:
    from guap_teacher_mcp.pages import validate_task_update

    # None everywhere = nothing to overlay, valid (the "at least one
    # parameter" guard lives in the tool itself).
    assert validate_task_update(None, None) is None
    assert validate_task_update("ЛР №2. Виджеты", 5) is None
    assert validate_task_update("ЛР №2. Виджеты", None) is None
    assert validate_task_update(None, 1) is None
    # name: blank or whitespace-only is rejected (None = don't touch).
    assert validate_task_update("") == "name не может быть пустым"
    assert validate_task_update("   ") == "name не может быть пустым"
    # max_ball (the form's markpoint field) must be an integer >= 1.
    assert (
        validate_task_update(None, 0) == "max_ball должен быть целым числом не меньше 1"
    )
    assert (
        validate_task_update(None, -3)
        == "max_ball должен быть целым числом не меньше 1"
    )


def test_parse_filter_options_only() -> None:
    opts_all = parse_filter_options(SCHEDULE_WEEK_HTML)
    assert set(opts_all) == {"group", "teacher"}
    opts_one = parse_filter_options(SCHEDULE_WEEK_HTML, only=["teacher"])
    assert set(opts_one) == {"teacher"}
    assert opts_one["teacher"][1] == {"value": "40734", "label": "Парамонов К.В."}
    assert parse_filter_options(SCHEDULE_WEEK_HTML, only=[]) == {}


def test_parse_reports_filters_param() -> None:
    data = parse_reports(REPORTS_HTML, filters=[])
    assert data["filter_options"] == {}
    data = parse_reports(REPORTS_HTML, filters=["status"])
    assert set(data["filter_options"]) == {"status"}


STUDENT_PROFILE_HTML = """
<html><body>
<nav><a href="/inside/profile">Профиль</a></nav>
<h3 class="text-center">Ледневская Анастасия Андреевна</h3>
<h5>Институт/факультет: Институт информационных технологий и программирования</h5>
<h5>Группа: 4513МКз MAX</h5>
<h5>Номер студенческого билета/ зачетной книжки: 2025/4623</h5>
<h5>Форма обучения: заочная</h5>
<h5>Статус: Зачислен</h5>
<p>Контакты Email lednevskaia.a.a@example.com</p>
</body></html>
"""


def test_parse_student_profile() -> None:
    from guap_teacher_mcp.pages import parse_student_profile

    data = parse_student_profile(STUDENT_PROFILE_HTML)
    assert data["name"] == "Ледневская Анастасия Андреевна"
    assert data["fields"]["Группа"] == "4513МКз MAX"
    assert data["fields"]["Статус"] == "Зачислен"
    assert data["email"] == "lednevskaia.a.a@example.com"


TASK_SHOW_HTML = """
<html><body>
<h3 class="page__title">ЛР №1. Верстка виджетов</h3>
<h5>Дисциплина: Распределенные информационные системы (4513МКз)</h5>
<h5>Макс. баллы за задание: 10</h5>
<h5>Предельная дата выполнения: не указана</h5>
<a href="/inside/subjects/3423947">Распределенные информационные системы</a>
<a href="/inside/professor/tasks/28/187688/edit">Редактировать</a>
<a href="/inside/professor/tasks/187688/remove">Удалить</a>
<table class="table table-bordered">
  <tr><th>п.н.</th><th>ФИО</th><th>Оценка</th><th>Загрузить отчет</th></tr>
  <tr><td>1</td><td>Агеева Ольга Сергеевна (Зачислен)</td><td></td>
      <td><a href="/inside/professor/reports/187688/56289/create">создать</a></td></tr>
  <tr><td>2</td><td>Бойцов Александр Валерьевич (Зачислен)</td><td></td>
      <td><a href="/inside/professor/reports/187688/56298/create">создать</a></td></tr>
  <tr><td>3</td><td>Виноградова Вера-Надежда Борисовна (Зачислен)</td><td></td>
      <td><a href="/inside/professor/reports/187688/45801/create">создать</a></td></tr>
</table>
<table class="table table-bordered table-striped">
  <tr><th>Студент</th><th>Статус</th><th>Дата загрузки</th><th>Дата проверки</th>
      <th>Комментарий студента</th><th>Комментарий преподавателя</th><th>Действия</th></tr>
  <tr>
    <td><a href="/inside/profile/56341">Ледневская Анастасия Андреевна</a></td>
    <td>принят 8 из 10</td><td>12:28:01 13.09.2026</td><td>10:00:00 20.09.2026</td>
    <td></td><td>хорошо</td>
    <td><a href="/inside/professor/reports/5668357/edit">править</a>
        <a href="/inside/professor/reports/5668357/download">скачать</a></td>
  </tr>
  <tr>
    <td><a href="/inside/profile/56347">Мошно Николай Константинович</a></td>
    <td>ожидает проверки</td><td>02:14:58 01.10.2026</td><td></td><td></td><td></td>
    <td><a href="/inside/professor/reports/5697049/edit">править</a>
        <a href="/inside/professor/reports/5697049/download">скачать</a></td>
  </tr>
  <tr>
    <td><a href="/inside/profile/56289">Агеева Ольга Сергеевна</a></td>
    <td>принят 7 из 10</td><td>09:00:00 05.09.2026</td><td>10:00:00 06.09.2026</td>
    <td></td><td></td>
    <td><a href="/inside/professor/reports/5668000/edit">править</a>
        <a href="/inside/professor/reports/5668000/download">скачать</a></td>
  </tr>
</table>
</body></html>
"""


def test_parse_task_card() -> None:
    from guap_teacher_mcp.pages import parse_task_card

    data = parse_task_card(TASK_SHOW_HTML)
    assert data["title"] == "ЛР №1. Верстка виджетов"
    assert data["fields"]["Макс. баллы за задание"] == "10"
    assert data["subject_id"] == 3423947
    assert data["manage"]["edit_url"] == "/inside/professor/tasks/28/187688/edit"
    assert data["manage"]["remove_url"] == "/inside/professor/tasks/187688/remove"

    assert len(data["reports"]) == 3
    first = data["reports"][0]
    assert first["student"] == "Ледневская Анастасия Андреевна"
    assert first["student_id"] == 56341
    assert first["report_id"] == 5668357
    assert first["status"] == "принят 8 из 10"
    assert first["mark"] == 8 and first["max_mark"] == 10
    assert first["teacher_comment"] == "хорошо"
    assert first["download_url"] == "/inside/professor/reports/5668357/download"
    second = data["reports"][1]
    assert second["mark"] is None and second["status"] == "ожидает проверки"
    assert second["download_url"] == "/inside/professor/reports/5697049/download"

    assert data["students"] == [
        {"student": "Агеева Ольга Сергеевна", "student_id": 56289},
        {"student": "Бойцов Александр Валерьевич", "student_id": 56298},
        {"student": "Виноградова Вера-Надежда Борисовна", "student_id": 45801},
    ]
    # not_submitted = course students minus the submitted-reports table;
    # create links exist for EVERY student (upload action), so they must
    # not be treated as "hasn't submitted" markers.
    assert data["not_submitted"] == [
        {"student": "Бойцов Александр Валерьевич", "student_id": 56298},
        {"student": "Виноградова Вера-Надежда Борисовна", "student_id": 45801},
    ]


GROUP_GRADES_HTML = """
<html><body>
<h1>Список группы</h1>
<p>Группа 4617</p>
<table>
  <tr><th>ФИО</th><th>ЛР №1 ТЗ</th><th>ЛР №2</th><th>Итого</th></tr>
  <tr><td>Амбарцумян С. Э.</td><td>принят  (5)</td><td>принят  (4)</td><td>9 из 20</td></tr>
  <tr><td>Носов А. С.</td><td></td><td></td><td>0 из 20</td></tr>
</table>
</body></html>
"""


def test_parse_group_grades() -> None:
    from guap_teacher_mcp.pages import parse_group_grades

    data = parse_group_grades(GROUP_GRADES_HTML)
    assert data["group"] == "4617"
    assert data["task_columns"] == ["ЛР №1 ТЗ", "ЛР №2"]
    first, second = data["rows"]
    assert first["name"] == "Амбарцумян С. Э."
    assert first["marks"][0] == {"task": "ЛР №1 ТЗ", "status": "принят", "mark": 5}
    assert first["total_mark"] == 9 and first["total_max"] == 20
    assert second["marks"][0]["mark"] is None
    assert second["marks"][0]["status"] is None
    assert second["total_mark"] == 0


TASK_EDIT_HTML = """
<html><body>
<form action="/inside/professor/tasks/187688?semesters=28&amp;_method=PUT"
      method="post" enctype="multipart/form-data">
  <input type="hidden" name="token" value="csrf-1"/>
  <select name="semesters">
    <option value="27">2025/2026 весенний</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
  <select name="subjects[]" multiple="multiple"></select>
  <select name="types">
    <option value="2" selected>Лабораторная работа</option>
  </select>
  <select name="groups[]" multiple="multiple"></select>
  <input name="name" type="text" value="ЛР №1. Верстка виджетов"/>
  <textarea name="description">Описание задания</textarea>
  <input name="markpoint" type="number" value="10"/>
  <select name="extensions[]" multiple="multiple">
    <option value="pdf" selected>pdf</option>
    <option value="docx">docx</option>
  </select>
  <input name="harddeadline" type="date" value=""/>
  <input type="checkbox" name="expulsionLine"/>
  <input type="checkbox" name="public" checked/>
  <input type="checkbox" name="reportRequired" checked/>
  <input type="file" name="file"/>
  <input type="hidden" name="file-deleted" value=""/>
</form>
</body></html>
"""


def test_parse_form_fields_task_edit() -> None:
    from guap_teacher_mcp.pages import TASK_UPDATE_ACTION_RE, parse_form_fields

    data = parse_form_fields(TASK_EDIT_HTML, TASK_UPDATE_ACTION_RE)
    assert data["action"] == "/inside/professor/tasks/187688?semesters=28&_method=PUT"
    assert data["enctype"] == "multipart/form-data"
    values = data["values"]
    assert values["token"] == "csrf-1"
    assert values["semesters"] == "28"
    assert values["types"] == "2"
    assert values["name"] == "ЛР №1. Верстка виджетов"
    assert values["description"] == "Описание задания"
    assert values["markpoint"] == "10"
    assert values["harddeadline"] == ""
    assert values["extensions[]"] == ["pdf"]
    assert data["checkboxes"] == {
        "expulsionLine": False,
        "public": True,
        "reportRequired": True,
    }
    # file inputs are never replayed
    assert "file" not in values
    assert data["selects"]["semesters"]["selected"] == "28"


MATERIALS_CREATE_HTML = """
<html><body>
<form action="/inside/professor/materials/store?id=0&amp;_method=POST"
      method="post" enctype="multipart/form-data">
  <input type="hidden" name="token" value="csrf-2"/>
  <input name="name" type="text" value=""/>
  <select name="semesters">
    <option value="29">2026/2027 весенний</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
  <select name="subjects[]" multiple="multiple"></select>
  <select name="groups[]" multiple="multiple"></select>
  <input type="checkbox" name="isPublic"/>
  <input type="checkbox" name="isNeedNotification" checked/>
  <input name="url" type="text" value=""/>
  <input type="file" name="file"/>
  <input type="hidden" name="file-deleted" value=""/>
</form>
</body></html>
"""


def test_parse_form_fields_materials_create() -> None:
    from guap_teacher_mcp.pages import MATERIALS_STORE_ACTION_RE, parse_form_fields

    data = parse_form_fields(MATERIALS_CREATE_HTML, MATERIALS_STORE_ACTION_RE)
    assert data["action"] == "/inside/professor/materials/store?id=0&_method=POST"
    assert data["values"]["semesters"] == "28"
    assert data["checkboxes"] == {"isPublic": False, "isNeedNotification": True}
    assert "file" not in data["values"]


def test_parse_form_fields_no_form() -> None:
    from guap_teacher_mcp.pages import TASK_UPDATE_ACTION_RE, parse_form_fields

    assert parse_form_fields("<html><body>нет формы</body></html>", TASK_UPDATE_ACTION_RE) == {}


NOTICE_LIST_HTML = """
<html><body>
<form method="get" action="/inside/professor/notice/new">
  <select name="semester">
    <option value="29">2026/2027 весенний</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
  <select name="perPage"><option value="10" selected="selected">10</option></select>
</form>
<table class="table table-bordered table-striped table-hover">
  <tr><th>№</th><th>Заголовок</th><th>Название дисциплины</th><th>Группа</th>
      <th>Активность</th><th>Описание</th><th>Дата создания</th>
      <th>Время показа c</th><th>Время показа по</th><th>Действия</th></tr>
  <tr>
    <td>1</td>
    <td>Созвон вместо отмененных занятий</td>
    <td><a class="link" target="_blank" href="/inside/subjects/3446314">
        Основы проектной деятельности в профессии (4615, 4616, 4617, 4614, 4618)</a></td>
    <td class="text-center"><a target="_blank" class="link badge bg-secondary"
        href="/inside/groups/7844/info">4617</a></td>
    <td class="text-center">
        <i class="fa fa-solid fa-eye-slash fs-6 text-danger" title="Не активно"></i></td>
    <td><span title="День добрый!
подключаемся сегодня (29.10.2026) в 19:30">День добрый!
подключаемся...</span></td>
    <td><span class="badge bg-secondary">11:01:29 29.10.2026</span></td>
    <td><span class="badge bg-secondary">10:59:00 29.10.2026</span></td>
    <td><span class="badge bg-secondary">21:00:00 29.10.2026</span></td>
    <td class="text-center"><div class="btn-group">
        <a title="Показать" href="/inside/professor/notice/51190/28"><i class="fa fa-eye"></i></a>
        <a title="Копировать" href="/inside/professor/notice/51190/28/copy"></a>
        <a title="Удалить" href="/inside/professor/notice/51190/28/remove"></a>
        <a title="Редактировать" href="/inside/professor/notice/51190/28/edit"></a>
    </div></td>
  </tr>
  <tr>
    <td>3</td>
    <td>Продолжение мастер-класса по работе с ИИ-агентами + прием лаб у 4617</td>
    <td><a class="link" target="_blank" href="/inside/subjects/3446314">
        Основы проектной деятельности в профессии (4615, 4616, 4617, 4614, 4618)</a></td>
    <td class="text-center"><a target="_blank" class="link badge bg-secondary"
        href="/inside/groups/7844/info">4617</a>
        <a target="_blank" class="link badge bg-secondary"
        href="/inside/groups/8039/info">4618</a></td>
    <td class="text-center">
        <i class="fa fa-solid fa-eye-slash fs-6 text-danger" title="Не активно"></i></td>
    <td><span title="Ссылка на подключение к созвону https://vk.ru/call/join/YsSN">Ссылка на подключение к созвону https://vk.ru/call...</span></td>
    <td><span class="badge bg-secondary">22:56:02 12.10.2026</span></td>
    <td><span class="badge bg-secondary">22:54:00 12.10.2026</span></td>
    <td><span class="badge bg-secondary">22:54:00 15.10.2026</span></td>
    <td class="text-center"><div class="btn-group">
        <a title="Показать" href="/inside/professor/notice/50998/28"><i class="fa fa-eye"></i></a>
        <a title="Копировать" href="/inside/professor/notice/50998/28/copy"></a>
        <a title="Удалить" href="/inside/professor/notice/50998/28/remove"></a>
        <a title="Редактировать" href="/inside/professor/notice/50998/28/edit"></a>
    </div></td>
  </tr>
</table>
</body></html>
"""


def test_parse_notices_rows_and_filters() -> None:
    from guap_teacher_mcp.pages import parse_notices

    data = parse_notices(NOTICE_LIST_HTML)
    assert data["count"] == 2
    first, second = data["notices"]
    assert first["notice_id"] == 51190
    assert first["title"] == "Созвон вместо отмененных занятий"
    assert first["subject"].startswith("Основы проектной деятельности")
    assert first["subject_id"] == 3446314
    assert first["groups"] == [{"group_id": 7844, "name": "4617"}]
    # the activity cell holds only a tooltip icon
    assert first["active"] == "Не активно"
    # the cell text is truncated on the portal — the full text lives in
    # the span title attribute
    assert first["description"].startswith("День добрый!")
    assert "в 19:30" in first["description"]
    assert first["created_at"] == "11:01:29 29.10.2026"
    assert first["show_from"] == "10:59:00 29.10.2026"
    assert first["show_until"] == "21:00:00 29.10.2026"
    assert first["actions"] == {
        "view": "/inside/professor/notice/51190/28",
        "edit": "/inside/professor/notice/51190/28/edit",
        "copy": "/inside/professor/notice/51190/28/copy",
        "remove": "/inside/professor/notice/51190/28/remove",
    }
    # a notice can target several groups
    assert second["groups"] == [
        {"group_id": 7844, "name": "4617"},
        {"group_id": 8039, "name": "4618"},
    ]
    assert set(data["filter_options"]) == {"semester"}
    assert parse_notices(NOTICE_LIST_HTML, filters=[])["filter_options"] == {}


NOTICE_CARD_HTML = """
<html><body>
<h3 class="page__title mb-3"> Объявление </h3>
<div class="form-group">
  <label for="semester">Семестр:</label>
  <select id="semester" name="semester" disabled="1">
    <option value="0">Все</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
</div>
<div class="form-group">
  <label for="idepc">Название дисциплины:</label>
  <select id="idepc" name="idepc[]" multiple="multiple" disabled="1">
    <option value="3419299">Автоматизация проектирования интернет-приложений (4513МК)</option>
    <option value="3446314" selected>Основы проектной деятельности в профессии (4617, 4618)</option>
  </select>
</div>
<div class="form-group">
  <label for="grid">Группы:</label>
  <select id="grid" name="grid[]" multiple="multiple" disabled="1"></select>
</div>
<div class="form-group">
  <label for="type">Тип:</label>
  <select id="type" name="type" disabled="1">
    <option value="info">Информация</option>
    <option value="danger" selected>Важное</option>
  </select>
</div>
<div class="form-group">
  <label for="title">Заголовок:</label>
  <input id="title" name="title" type="text" value="Мастер-класс по работе с ИИ-агентами" disabled="1">
</div>
<div class="form-group form-group-sm">
  <label for="descr">Описание:</label>
  <textarea id="descr" name="descr" disabled="1">Добрый день!
Ссылка для подключения: https://vk.ru/call/join/bPn9</textarea>
</div>
<div class="form-group">
  <label for="startDatetime">Дата начала показа:</label>
  <input id="startDatetime" type="datetime-local" name="startDatetime"
         value="2026-10-11T17:55" disabled="1">
</div>
<div class="form-group">
  <label for="endDatetime">Дата окончания показа:</label>
  <input id="endDatetime" type="datetime-local" name="endDatetime"
         value="2026-10-12T22:00" disabled="1">
</div>
<div class="form-group">
  <label for="upload">Файл:</label>
  <input id="upload" type="file" name="upload" class="d-none">
</div>
<a class="btn btn-sm btn-success" href="/inside/professor/notice/50994/28/edit">Редактировать</a>
<a class="btn btn-sm btn-danger" href="/inside/professor/notice/50994/28/remove">Удалить</a>
<a href="/inside/professor/notice/new" class="btn btn-sm btn-outline-info">Отмена</a>
<table class="table table-bordered align-middle table-striped mb-0">
  <tr><th>№</th><th style="width: 150px;">ФИО</th><th><span>Статус</span></th></tr>
  <tr><td colspan="100" class="text-center"><h5><b>Группа 4618</b></h5></td></tr>
  <tr><td class="text-center">1</td>
      <td class="text-left"><a target="_blank" href="/inside/profile/59225">
          <span class="link-switch link-switch-blue">Ануфриев Михаил Романович</span></a></td>
      <td class="text-center text-success">прочитано</td></tr>
  <tr><td class="text-center">2</td>
      <td class="text-left"><a target="_blank" href="/inside/profile/59428">
          <span class="link-switch link-switch-blue">Горшкова Анна Евгеньевна</span></a></td>
      <td class="text-center text-danger">не прочитано</td></tr>
  <tr><td colspan="100" class="text-center"><h5><b>Группа 4617</b></h5></td></tr>
  <tr><td class="text-center">1</td>
      <td class="text-left"><a target="_blank" href="/inside/profile/57083">
          <span class="link-switch link-switch-blue">Амбарцумян Саргис Эдгарович</span></a></td>
      <td class="text-center text-success">прочитано</td></tr>
</table>
</body></html>
"""


def test_parse_notice_card_fields_groups_manage() -> None:
    from guap_teacher_mcp.pages import parse_notice_card

    data = parse_notice_card(NOTICE_CARD_HTML, notice_id=50994)
    assert data["title"] == "Объявление"
    fields = data["fields"]
    assert fields["Семестр"] == "2026/2027 осенний"
    assert fields["Название дисциплины"] == [
        "Основы проектной деятельности в профессии (4617, 4618)"
    ]
    # grid[] select is populated by JS and stays empty in the HTML
    assert fields["Группы"] == []
    assert fields["Тип"] == "Важное"
    assert fields["Заголовок"] == "Мастер-класс по работе с ИИ-агентами"
    assert fields["Описание"] == (
        "Добрый день!\nСсылка для подключения: https://vk.ru/call/join/bPn9"
    )
    assert fields["Дата начала показа"] == "2026-10-11T17:55"
    assert fields["Дата окончания показа"] == "2026-10-12T22:00"
    # file inputs are never reported
    assert "Файл" not in fields

    # one table, groups are the h5 "Группа N" separator rows
    assert data["groups"] == [
        {
            "label": "Группа 4618",
            "students": [
                {"name": "Ануфриев Михаил Романович", "status": "прочитано"},
                {"name": "Горшкова Анна Евгеньевна", "status": "не прочитано"},
            ],
        },
        {
            "label": "Группа 4617",
            "students": [
                {"name": "Амбарцумян Саргис Эдгарович", "status": "прочитано"},
            ],
        },
    ]
    assert data["manage"]["edit_url"] == "/inside/professor/notice/50994/28/edit"
    assert data["manage"]["remove_url"] == "/inside/professor/notice/50994/28/remove"
    # the card page carries no copy link (it exists only in the list)
    assert data["manage"]["copy_url"] is None


GROUP_INFO_HTML = """
<html><body>
<h3 class="page__title m-0">Группа 4617</h3>
<div class="list-group-item"><h5>Статус:
    <span class="fw-light lh-base">активная</span></h5></div>
<div class="list-group-item"><h5>Год:
    <span class="fw-light lh-base"> 2026</span></h5></div>
<h4>Список группы</h4>
<table class="table table-bordered align-middle table-striped mb-0">
  <tr><th>№</th><th style="width: 150px;">ФИО</th><th><span>Статус</span></th>
      <th><span>Номер студенческого</span></th><th><span>Средний балл</span></th></tr>
  <tr><td class="text-center">1</td>
      <td class="text-left"><a target="_blank" href="/inside/profile/57083">
          <span class="link-switch link-switch-blue">Амбарцумян Саргис Эдгарович</span></a></td>
      <td class="text-left">Зачислен</td>
      <td class="text-left">2026/1089</td>
      <td class="text-center">0</td></tr>
  <tr><td class="text-center">2</td>
      <td class="text-left"><a target="_blank" href="/inside/profile/59252">
          <span class="link-switch link-switch-blue">Балашов Андрей Дмитриевич</span></a></td>
      <td class="text-left">Зачислен</td>
      <td class="text-left">2026/3789</td>
      <td class="text-center">0</td></tr>
</table>
</body></html>
"""


def test_parse_group_info_students() -> None:
    from guap_teacher_mcp.pages import parse_group_info

    data = parse_group_info(GROUP_INFO_HTML)
    assert data["group"] == "4617"
    assert data["students"] == [
        {
            "name": "Амбарцумян Саргис Эдгарович",
            "status": "Зачислен",
            "student_card": "2026/1089",
            "avg_mark": "0",
        },
        {
            "name": "Балашов Андрей Дмитриевич",
            "status": "Зачислен",
            "student_card": "2026/3789",
            "avg_mark": "0",
        },
    ]


TASK_REPORTS_DOWNLOAD_HTML = """
<html><body>
<h3 class="fw-lighter">ЛР</h3>
<h5 class="fw-bold">Дисциплина:
    <a class="fw-light" href="/inside/subjects/3419299">
        Автоматизация проектирования интернет-приложений (4513МК)</a></h5>
<table class="table table-bordered table-striped">
  <tr><th><a href="/inside/professor/tasks/192715/show?sort=student">Студент</a></th>
      <th><a href="/inside/professor/tasks/192715/show?sort=status">Статус</a></th>
      <th><a href="/inside/professor/tasks/192715/show?sort=dateUpload">Дата загрузки</a></th>
      <th><a href="/inside/professor/tasks/192715/show?sort=dateCheck">Дата проверки</a></th>
      <th>Комментарий студента</th><th>Комментарий преподавателя</th><th>Действия</th></tr>
  <tr>
    <td><a href="/inside/profile/37004">Пластинин Евгений Алексеевич</a></td>
    <td class="text-center text-nowrap"><span class="text-success">принят
        (30 баллов)</span></td>
    <td class="text-center">21:36:52 10.10.2026</td>
    <td class="text-center"><span>23:20:53 09.11.2026</span></td>
    <td></td><td></td>
    <td class="text-center"><div class="btn-group">
        <a title="Смотреть отчет" href="/inside/professor/reports/5717534/edit">
            <i class="fa fa-eye"></i></a>
        <a title="Скачать отчет" href="/inside/professor/reports/5717534/download" target="_blank">
            <i class="fa fa-download"></i></a>
    </div></td>
  </tr>
</table>
</body></html>
"""


def test_parse_task_card_report_download_url() -> None:
    from guap_teacher_mcp.pages import parse_task_card

    data = parse_task_card(TASK_REPORTS_DOWNLOAD_HTML)
    assert data["subject_id"] == 3419299
    assert len(data["reports"]) == 1
    report = data["reports"][0]
    assert report["student_id"] == 37004
    assert report["report_id"] == 5717534
    assert report["download_url"] == "/inside/professor/reports/5717534/download"
    # real 2026-11 status format: «принят (30 баллов)» — no "N из M",
    # so mark/max_mark stay None while the status text is kept as-is
    assert report["status"] == "принят (30 баллов)"
    assert report["mark"] is None and report["max_mark"] is None


def test_parse_materials_extracts_material_id_and_edit_url() -> None:
    data = parse_materials(MATERIALS_HTML)
    assert data["count"] == 1
    row = data["materials"][0]
    # The edit action link /inside/professor/materials/{sem}/{id}/edit is
    # the id source; copy/remove links in the same cell must not match.
    assert row["material_id"] == 113620
    assert row["edit_url"] == "/inside/professor/materials/28/113620/edit"


MATERIAL_EDIT_HTML = """
<html><body>
<form action="/inside/professor/materials/113620?_method=PUT" id="materialEdit"
      method="post" enctype="multipart/form-data">
  <input type="hidden" name="token" value="csrf-3"/>
  <input id="name" name="name" type="text" value="Учебные материалы"/>
  <select id="semesters" name="semesters">
    <option value="29">2026/2027 весенний</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
  <select id="subjects" name="subjects[]" multiple="multiple"></select>
  <select id="groups" name="groups[]" multiple="multiple"></select>
  <input id="isPublic-isPublic" type="checkbox" name="isPublic" checked/>
  <input id="isNeedNotification-isNeedNotification" type="checkbox"
         name="isNeedNotification" checked/>
  <input id="url" name="url" type="text" value=""/>
  <input id="file-upload" type="file" name="file"/>
  <input id="file-deleted" type="hidden" name="file-deleted" value=""/>
</form>
</body></html>
"""


def test_parse_form_fields_material_edit() -> None:
    from guap_teacher_mcp.pages import MATERIAL_UPDATE_ACTION_RE, parse_form_fields

    data = parse_form_fields(MATERIAL_EDIT_HTML, MATERIAL_UPDATE_ACTION_RE)
    # action keeps the ?_method=PUT query (POST + Laravel method override)
    assert data["action"] == "/inside/professor/materials/113620?_method=PUT"
    assert data["enctype"] == "multipart/form-data"
    values = data["values"]
    assert values["token"] == "csrf-3"
    assert values["name"] == "Учебные материалы"
    assert values["semesters"] == "28"
    assert values["url"] == ""
    assert values["file-deleted"] == ""
    assert values["subjects[]"] == []
    assert values["groups[]"] == []
    assert data["checkboxes"] == {"isPublic": True, "isNeedNotification": True}
    # file inputs are never replayed
    assert "file" not in values


NOTICE_CREATE_HTML = """
<html><body>
<form method="post" action="/inside/professor/notice/" enctype="multipart/form-data">
  <input type="hidden" name="token" value="csrf-4"/>
  <input type="hidden" name="semester" value="28"/>
  <select id="semester" name="semester">
    <option value="29">2026/2027 весенний</option>
    <option value="28" selected>2026/2027 осенний</option>
  </select>
  <select id="idepc" name="idepc[]" multiple="multiple">
    <option value="3419299">Автоматизация проектирования интернет-приложений (4513МК) (Э)</option>
    <option value="3423947">Распределенные информационные системы (4513МКз) (Э)</option>
  </select>
  <select id="grid" name="grid[]" multiple="multiple"></select>
  <select id="type" name="type">
    <option value="info">Информация</option>
    <option value="danger">Важное</option>
    <option value="warning">Предупреждение</option>
    <option value="succes">Поздравление</option>
  </select>
  <input id="title" name="title" type="text" value=""/>
  <textarea id="descr" name="descr"></textarea>
  <input id="startDatetime" type="datetime-local" name="startDatetime"
         value="2026-11-10T15:31"/>
  <input id="endDatetime" type="datetime-local" name="endDatetime"
         value="2026-11-10T15:31"/>
  <input id="upload" type="file" name="upload"/>
  <input id="upload-deleted" type="hidden" name="upload-deleted" value=""/>
</form>
</body></html>
"""


def test_parse_form_fields_notice_create() -> None:
    from guap_teacher_mcp.pages import NOTICE_STORE_ACTION_RE, parse_form_fields

    data = parse_form_fields(NOTICE_CREATE_HTML, NOTICE_STORE_ACTION_RE)
    assert data["action"] == "/inside/professor/notice/"
    assert data["enctype"] == "multipart/form-data"
    values = data["values"]
    assert values["token"] == "csrf-4"
    # the hidden input comes first, so it wins over the same-named select
    assert values["semester"] == "28"
    assert values["title"] == ""
    assert values["descr"] == ""
    assert values["startDatetime"] == "2026-11-10T15:31"
    assert values["endDatetime"] == "2026-11-10T15:31"
    assert values["upload-deleted"] == ""
    assert values["idepc[]"] == []
    assert values["grid[]"] == []
    # no option is preselected -> nothing to replay for the type
    assert values["type"] is None
    assert data["selects"]["type"]["options"] == [
        {"value": "info", "label": "Информация"},
        {"value": "danger", "label": "Важное"},
        {"value": "warning", "label": "Предупреждение"},
        # the portal's own spelling of "succes" is kept verbatim
        {"value": "succes", "label": "Поздравление"},
    ]
    # file inputs are never replayed
    assert "upload" not in values
    assert data["checkboxes"] == {}


def test_resolve_notice_type() -> None:
    from guap_teacher_mcp.pages import KNOWN_NOTICE_TYPES, resolve_notice_type

    assert resolve_notice_type("danger") == {"value": "danger", "label": "Важное"}
    assert resolve_notice_type("Поздравление") == {
        "value": "succes",
        "label": "Поздравление",
    }
    assert resolve_notice_type("succes") == {
        "value": "succes",
        "label": "Поздравление",
    }
    assert resolve_notice_type("предупреждение") == {
        "value": "warning",
        "label": "Предупреждение",
    }
    assert resolve_notice_type("мусор") is None
    # page options take precedence over the known list
    page_options = [{"value": "custom", "label": "Особое"}]
    assert resolve_notice_type("Особое", page_options) == {
        "value": "custom",
        "label": "Особое",
    }
    assert KNOWN_NOTICE_TYPES[3] == {"value": "succes", "label": "Поздравление"}


def test_parse_notices_default_semester() -> None:
    from guap_teacher_mcp.pages import parse_notices

    html = """
    <select name="semester">
      <option value="29">2026/2027 весенний</option>
      <option value="28" selected>2026/2027 осенний</option>
    </select>
    """
    # the default semester feeds create_notice's semester fallback
    assert parse_notices(html)["default_semester"] == "28"


# Minimal synthetic subject cards for parse_subject_groups: no real
# student names or card numbers, only the link layout of the portal.
SUBJECT_CARD_CLASSIC_HTML = """
<html><body>
<h3 class="page__title">Классическая дисциплина</h3>
<h5>Группы: <a target="_blank" class="link" href="/inside/groups/7432/info">4514</a>,
    <a target="_blank" class="link" href="/inside/groups/7433/info?referer=card">4515</a></h5>
<h4>Ведомости</h4>
<table class="table table-bordered table-striped">
  <tr><th>Группа</th><th>Действия</th></tr>
  <tr><td><a target="_blank" href="/inside/groups/7432/info">4514</a></td>
      <td><a target="_blank" href="/inside/groups/3419299/7432">Печать</a></td></tr>
  <tr><td><a target="_blank" href="/inside/groups/7433/info">4515</a></td>
      <td><a target="_blank" href="/inside/groups/3419299/7433">Печать</a></td></tr>
</table>
</body></html>
"""

# ИТ-модуль cards have no grade-sheet («Печать») links at all: the
# «Ведомости» tables and the h5 «Группы» line carry only info links.
SUBJECT_CARD_IT_MODULE_HTML = """
<html><body>
<h3 class="page__title">ИТ-модуль &laquo;Программирование на языке Python&raquo;</h3>
<h5>Группы: <a target="_blank" class="link" href="/inside/groups/7071/info">2436</a> (12 чел.),
    <a target="_blank" class="link" href="/inside/groups/7070/info">2435</a> (15 чел.)</h5>
<h4>Ведомости</h4>
<table class="table table-bordered table-striped">
  <tr><th>Группа</th><th>Тип</th></tr>
  <tr><td><a target="_blank" href="/inside/groups/7070/info">2435</a></td><td>Зачёт</td></tr>
  <tr><td><a target="_blank" href="/inside/groups/7071/info">2436</a></td><td>Зачёт</td></tr>
</table>
</body></html>
"""

# A card may mix both layouts: one group with a grade sheet, others
# visible only through their info links.
SUBJECT_CARD_MIXED_HTML = """
<html><body>
<h3 class="page__title">Смешанная карточка</h3>
<h5>Группы: <a target="_blank" class="link" href="/inside/groups/7275/info">3426</a>,
    <a target="_blank" class="link" href="/inside/groups/7277/info">3428</a>,
    <a target="_blank" class="link" href="/inside/groups/7278/info">3429</a></h5>
<h4>Ведомости</h4>
<table class="table table-bordered table-striped">
  <tr><th>Группа</th><th>Действия</th></tr>
  <tr><td><a target="_blank" href="/inside/groups/7275/info">3426</a></td>
      <td><a target="_blank" href="/inside/groups/3432843/7275">Печать</a></td></tr>
</table>
<table class="table table-bordered table-striped">
  <tr><th>Группа</th><th>Тип</th></tr>
  <tr><td><a target="_blank" href="/inside/groups/7277/info">3428</a></td><td>Зачёт</td></tr>
  <tr><td><a target="_blank" href="/inside/groups/7278/info">3429</a></td><td>Зачёт</td></tr>
</table>
</body></html>
"""


def test_parse_subject_groups_classic_print_links() -> None:
    from guap_teacher_mcp.pages import parse_subject_groups

    groups = parse_subject_groups(SUBJECT_CARD_CLASSIC_HTML, 3419299)
    assert groups == [
        {
            "group_id": 7432,
            "name": "4514",
            "grade_sheet_url": "/inside/groups/3419299/7432",
        },
        {
            "group_id": 7433,
            "name": "4515",
            "grade_sheet_url": "/inside/groups/3419299/7433",
        },
    ]


def test_parse_subject_groups_it_module_info_links_only() -> None:
    from guap_teacher_mcp.pages import parse_subject_groups

    groups = parse_subject_groups(SUBJECT_CARD_IT_MODULE_HTML, 3432756)
    # no «Печать» links on the card: groups come from the info links,
    # grade_sheet_url is None, entries deduplicated by gid and sorted
    assert groups == [
        {"group_id": 7070, "name": "2435", "grade_sheet_url": None},
        {"group_id": 7071, "name": "2436", "grade_sheet_url": None},
    ]


def test_parse_subject_groups_mixed_markup() -> None:
    from guap_teacher_mcp.pages import parse_subject_groups

    groups = parse_subject_groups(SUBJECT_CARD_MIXED_HTML, 3432843)
    # the group with a grade-sheet link keeps it; info-only groups get
    # grade_sheet_url=None; the gid seen in both the h5 line and the
    # table yields a single entry
    assert groups == [
        {
            "group_id": 7275,
            "name": "3426",
            "grade_sheet_url": "/inside/groups/3432843/7275",
        },
        {"group_id": 7277, "name": "3428", "grade_sheet_url": None},
        {"group_id": 7278, "name": "3429", "grade_sheet_url": None},
    ]


def test_parse_subject_groups_no_groups() -> None:
    from guap_teacher_mcp.pages import parse_subject_groups

    assert parse_subject_groups(CARD_HTML, 3419299) == []
