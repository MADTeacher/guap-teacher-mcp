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
    <td><a href="/inside/professor/materials/999/edit"></a></td>
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
    assert "searchtext" not in data["filter_options"]


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
    second = data["reports"][1]
    assert second["mark"] is None and second["status"] == "ожидает проверки"

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
