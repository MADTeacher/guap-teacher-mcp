"""Pure HTML parsers for the teacher-facing pages of pro.guap.ru.

Every function takes an HTML string and returns plain data (dicts/lists),
so everything here is trivially testable on fixtures. Network access lives
in client.py, MCP wiring in server.py.

Known page layouts (verified 2026-11):

/inside/professor/reports     table: student, group, task, status, comments,
                              deadlines; row action links .../{id}/edit|download
/inside/professor/tasks       table: order, subject, name, type, deadline,
                              visibility, updated; links /show, /{sem}/{id}/edit
/inside/professor/materials   table: file link, subject, name, groups,
                              visibility, added
/inside/subjects/new          search form; results are /inside/subjects/{id}
                              links (a table is NOT used here); search only
                              fires when the `searchtext` param is present
/inside/subjects/{id}         card: h5 "Key: value" fields, groups, teachers
/inside/profile/{id}          student card: h3.text-center name + h5 fields,
                              contact email inside the page text
/inside/professor/tasks/{id}/show  h5 card + two tables: course students
                              (not-submitted rows carry .../reports/{task}/
                              {student}/create links) and submitted reports
/inside/professor/tasks/{sem}/{id}/edit  multipart form; subjects[]/groups[]
                              selects are empty select2 widgets (absent from
                              the POST = unchanged on the server)
/inside/professor/materials/create     multipart form (subjects[]/groups[]
                              supplied by the caller), file or external url
/inside/groups/{subject}/{group}       "Список группы" grade sheet: name,
                              per-task "принят (N)" cells, "N из M" total
/inside/students/classes/schedule/{day,week}/...  tables with pair/time and
                              per-day cells; filters: group, teacher,
                              building, room
"""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

SUBJECT_LINK_RE = re.compile(r"^/inside/subjects/(\d+)$")
REPORT_ACTION_RE = re.compile(r"^/inside/professor/reports/(\d+)/(edit|download)$")
REPORT_CREATE_RE = re.compile(r"^/inside/professor/reports/(\d+)/(\d+)/create$")
TASK_ACTION_RE = re.compile(r"^/inside/professor/tasks/(\d+)/show$")
TASK_EDIT_RE = re.compile(r"^/inside/professor/tasks/(\d+)/(\d+)/edit$")
TASK_REMOVE_RE = re.compile(r"^/inside/professor/tasks/(\d+)/remove$")
TASK_UPDATE_ACTION_RE = re.compile(r"^/inside/professor/tasks/(\d+)$")
MATERIALS_STORE_ACTION_RE = re.compile(r"^/inside/professor/materials/store$")
PROFILE_LINK_RE = re.compile(r"^/inside/profile/(\d+)$")

MARK_OF_RE = re.compile(r"(\d+)\s+из\s+(\d+)")
MARK_IN_PARENS_RE = re.compile(r"\((\d+)\)")
STATUS_PARENS_RE = re.compile(r"\s*\([^)]*\)\s*$")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _cell_text(cell) -> str:
    return re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()


def _first_table(html: str) -> Optional[BeautifulSoup]:
    return _soup(html).find("table")


def parse_filter_options(
    html: str, only: Optional[list[str]] = None
) -> dict[str, list[dict[str, str]]]:
    """Collect <select> filters as {name: [{value, label}]} (service selects skipped).

    `only` selects which filters to keep: None keeps everything (previous
    behaviour), an empty list drops all filter options (the schedule student
    filter alone is ~500 entries and can blow up the MCP response), and a
    list of names keeps just those filters.
    """
    skip = {"token", "switch", "perPage"}
    options: dict[str, list[dict[str, str]]] = {}
    for select in _soup(html).select("select[name]"):
        name = select.get("name")
        if name in skip or name in options:
            continue
        if only is not None and name not in only:
            continue
        options[name] = [
            {"value": opt.get("value", ""), "label": opt.get_text(" ", strip=True)}
            for opt in select.find_all("option")
        ]
    return options


def _selected_value(html: str, name: str) -> Optional[str]:
    select = _soup(html).select_one(f"select[name='{name}']")
    if select is None:
        return None
    selected = select.find("option", selected=True)
    if selected is not None:
        return selected.get("value")
    first = select.find("option")
    return first.get("value") if first else None


def parse_reports(html: str, filters: Optional[list[str]] = None) -> dict:
    """Parse /inside/professor/reports into rows + filter options."""
    table = _first_table(html)
    rows: list[dict] = []
    if table is not None:
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 10:
                continue
            report_id: Optional[int] = None
            download_url: Optional[str] = None
            for a in cells[0].find_all("a", href=True):
                match = REPORT_ACTION_RE.match(a["href"])
                if match:
                    report_id = int(match.group(1))
                    if match.group(2) == "download":
                        download_url = a["href"]
            student_link = cells[1].find("a", href=PROFILE_LINK_RE)
            task_link = cells[3].find("a", href=True)
            rows.append(
                {
                    "report_id": report_id,
                    "student": _cell_text(cells[1]),
                    "student_id": (
                        int(PROFILE_LINK_RE.match(student_link["href"]).group(1))
                        if student_link
                        else None
                    ),
                    "group": _cell_text(cells[2]),
                    "task": _cell_text(cells[3]),
                    "task_url": task_link["href"] if task_link else None,
                    "status": _cell_text(cells[4]),
                    "student_comment": _cell_text(cells[5]),
                    "teacher_comment": _cell_text(cells[6]),
                    "deadline": _cell_text(cells[7]),
                    "uploaded_at": _cell_text(cells[8]),
                    "checked_at": _cell_text(cells[9]),
                    "download_url": download_url,
                }
            )
    return {
        "count": len(rows),
        "reports": rows,
        "filter_options": parse_filter_options(html, filters),
    }


REPORT_FORM_RE = re.compile(r"^/inside/professor/reports/(\d+)$")

# The report edit form carries `status` as a plain field without <option>s;
# the enum comes from the status filter of /inside/professor/reports
# (verified 2026-11-09).
KNOWN_REPORT_STATUSES: list[dict[str, str]] = [
    {"value": "1", "label": "ожидает проверки"},
    {"value": "2", "label": "принят"},
    {"value": "3", "label": "не принят"},
]


def resolve_report_status(
    status: str, options: Optional[list[dict[str, str]]] = None
) -> Optional[dict[str, str]]:
    """Resolve a status given as a value or a label to {value, label}.

    `options` defaults to KNOWN_REPORT_STATUSES; pass the parsed form's
    status_options to prefer the page's own list when it has one.
    """
    for option in options if options else KNOWN_REPORT_STATUSES:
        if status == option["value"] or status.lower() == option["label"].lower():
            return option
    return None


def parse_report_review_form(html: str, report_id: Optional[int] = None) -> dict:
    """Parse the report review form (GET /inside/professor/reports/{id}/edit).

    Returns {"fields": {name: current value}, "status_options": [...]},
    where fields carries every input/textarea value (token, _method,
    taskId, student, ...) needed to submit the form, and status_options
    lists the status <select> options as {value, label}.
    """
    soup = _soup(html)
    form = None
    for candidate in soup.find_all("form", action=True):
        match = REPORT_FORM_RE.match(candidate["action"])
        if match and (report_id is None or int(match.group(1)) == report_id):
            form = candidate
            break
    if form is None:
        return {"fields": {}, "status_options": []}

    fields: dict[str, str] = {}
    status_options: list[dict[str, str]] = []
    for node in form.find_all(["input", "select", "textarea"]):
        name = node.get("name")
        if not name or name in fields:
            continue
        if node.name == "select":
            for option in node.find_all("option"):
                status_options.append(
                    {"value": option.get("value", ""), "label": _cell_text(option)}
                )
            selected = node.find("option", selected=True)
            fields[name] = (selected.get("value", "") if selected else "") or ""
        elif node.get("type") in ("radio", "checkbox"):
            if node.get("checked") is not None:
                fields[name] = node.get("value", "")
        elif node.name == "textarea":
            fields[name] = node.get_text("", strip=True)
        else:
            fields[name] = node.get("value", "")
    return {"fields": fields, "status_options": status_options}


def parse_h5_card(html: str) -> dict[str, str]:
    """Parse a detail page (task/subject) built from h5 'Key: value' fields."""
    soup = _soup(html)
    title_node = soup.select_one("h3.page__title") or soup.select_one("h3")
    fields: dict[str, str] = {}
    for h5 in soup.find_all("h5"):
        text = h5.get_text(" ", strip=True)
        if ":" in text:
            key, _, value = text.partition(":")
            fields[key.strip()] = value.strip()
    return {
        "title": title_node.get_text(" ", strip=True) if title_node else None,
        "fields": fields,
    }


def parse_tasks(html: str, filters: Optional[list[str]] = None) -> dict:
    """Parse /inside/professor/tasks into rows + filter options."""
    table = _first_table(html)
    rows: list[dict] = []
    if table is not None:
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 8:
                continue
            task_id: Optional[int] = None
            for a in cells[0].find_all("a", href=True):
                match = TASK_ACTION_RE.match(a["href"])
                if match:
                    task_id = int(match.group(1))
                    break
            subject_link = cells[2].find("a", href=SUBJECT_LINK_RE)
            name_link = cells[3].find("a", href=True)
            rows.append(
                {
                    "task_id": task_id,
                    "order": _cell_text(cells[1]),
                    "subject": _cell_text(cells[2]),
                    "subject_id": (
                        int(SUBJECT_LINK_RE.match(subject_link["href"]).group(1))
                        if subject_link
                        else None
                    ),
                    "name": _cell_text(cells[3]),
                    "task_url": name_link["href"] if name_link else None,
                    "type": _cell_text(cells[4]),
                    "deadline": _cell_text(cells[5]),
                    "visible_to_students": bool(_cell_text(cells[6])),
                    "updated_at": _cell_text(cells[7]),
                }
            )
    return {
        "count": len(rows),
        "tasks": rows,
        "filter_options": parse_filter_options(html, filters),
    }


def parse_materials(html: str, filters: Optional[list[str]] = None) -> dict:
    """Parse /inside/professor/materials into rows + filter options."""
    table = _first_table(html)
    rows: list[dict] = []
    if table is not None:
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 7:
                continue
            file_link = cells[1].find("a", href=True)
            subject_link = cells[2].find("a", href=SUBJECT_LINK_RE)
            rows.append(
                {
                    "name": _cell_text(cells[3]),
                    "file_text": _cell_text(cells[1]),
                    "file_url": file_link["href"] if file_link else None,
                    "subject": _cell_text(cells[2]),
                    "subject_id": (
                        int(SUBJECT_LINK_RE.match(subject_link["href"]).group(1))
                        if subject_link
                        else None
                    ),
                    "groups": _cell_text(cells[4]),
                    "visible": bool(_cell_text(cells[5])),
                    "added_at": _cell_text(cells[6]),
                }
            )
    return {
        "count": len(rows),
        "materials": rows,
        "filter_options": parse_filter_options(html, filters),
    }


def parse_subjects(html: str) -> dict:
    """Parse /inside/subjects/new search results: /inside/subjects/{id} links."""
    soup = _soup(html)
    subjects: dict[int, str] = {}
    for a in soup.find_all("a", href=SUBJECT_LINK_RE):
        subject_id = int(SUBJECT_LINK_RE.match(a["href"]).group(1))
        subjects.setdefault(subject_id, a.get_text(" ", strip=True))
    return {
        "count": len(subjects),
        "subjects": [
            {"subject_id": sid, "name": name} for sid, name in subjects.items()
        ],
        "filter_options": parse_filter_options(html),
        "default_semester": _selected_value(html, "semester"),
    }


def parse_schedule(html: str, filters: Optional[list[str]] = None) -> dict:
    """Parse day/week schedule tables into lessons + filter options.

    Day view: rows of (pair, time, discipline cell).
    Week view: rows of (pair, time, one cell per weekday).
    Discipline cells are returned as {text, links} because the portal puts
    subject/room/teacher links inside.
    """
    table = _first_table(html)
    view: dict = {
        "headers": [],
        "rows": [],
        "filter_options": parse_filter_options(html, filters),
    }
    if table is None:
        return view

    header_cells = table.find_all("tr")[0].find_all(["th", "td"])
    view["headers"] = [_cell_text(c) for c in header_cells]

    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue
        day_cells = [
            {
                "text": _cell_text(cell),
                "links": [a["href"] for a in cell.find_all("a", href=True)],
            }
            for cell in cells[2:]
        ]
        view["rows"].append(
            {"pair": _cell_text(cells[0]), "time": _cell_text(cells[1]), "days": day_cells}
        )
    return view


def parse_student_profile(html: str) -> dict:
    """Parse a student profile card (GET /inside/profile/{id}).

    Returns {"name", "fields": {key: value}, "email"}: the name comes from
    h3.text-center, the h5 "Key: value" fields mirror other portal cards,
    and the contact email is the first address found in the page text.
    """
    soup = _soup(html)
    name_node = soup.select_one("h3.text-center")
    card = parse_h5_card(html)
    email_match = EMAIL_RE.search(soup.get_text(" ", strip=True))
    return {
        "name": name_node.get_text(" ", strip=True) if name_node else None,
        "fields": card["fields"],
        "email": email_match.group(0) if email_match else None,
    }


def parse_task_card(html: str) -> dict:
    """Parse a task card (GET /inside/professor/tasks/{id}/show).

    Combines the h5 "Key: value" card with the two tables below it:
    the course-student table (every row carries a .../reports/{task}/
    {student}/create link — it is just the "upload report" action, present
    for submitted students too, so student ids are taken from it but the
    links themselves never enter the result) and the submitted reports
    table (student, status, dates, comments, report actions). Students of
    the course minus the reports table = not_submitted.
    """
    soup = _soup(html)
    card = parse_h5_card(html)
    subject_id: Optional[int] = None
    manage: dict[str, Optional[str]] = {"edit_url": None, "remove_url": None}

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].split("?", 1)[0]
        subject_match = SUBJECT_LINK_RE.match(href)
        if subject_match and subject_id is None:
            subject_id = int(subject_match.group(1))
        edit_match = TASK_EDIT_RE.match(href)
        if edit_match:
            manage["edit_url"] = href
        remove_match = TASK_REMOVE_RE.match(href)
        if remove_match:
            manage["remove_url"] = href

    reports: list[dict] = []
    students: list[dict] = []
    for table in soup.find_all("table"):
        first_row = table.find("tr")
        if first_row is None:
            continue
        headers = [_cell_text(c) for c in first_row.find_all(["th", "td"])]
        if "Студент" in headers and "Действия" in headers:
            reports = _parse_task_reports_table(table)
        elif "ФИО" in headers and any("Загрузить отчет" in h for h in headers):
            students = _parse_task_students_table(table)

    submitted_ids = {row["student_id"] for row in reports if row["student_id"]}
    not_submitted = [
        row for row in students if row["student_id"] not in submitted_ids
    ]
    return {
        "title": card["title"],
        "fields": card["fields"],
        "subject_id": subject_id,
        "reports": reports,
        "students": students,
        "not_submitted": not_submitted,
        "manage": manage,
    }


def _parse_task_reports_table(table) -> list[dict]:
    """Rows of the submitted-reports table on a task card."""
    rows: list[dict] = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 7:
            continue
        student_link = cells[0].find("a", href=PROFILE_LINK_RE)
        status_text = _cell_text(cells[1])
        mark_match = MARK_OF_RE.search(status_text)
        report_id: Optional[int] = None
        for anchor in cells[6].find_all("a", href=True):
            action_match = REPORT_ACTION_RE.match(anchor["href"].split("?", 1)[0])
            if action_match and action_match.group(2) == "edit":
                report_id = int(action_match.group(1))
                break
        rows.append(
            {
                "student": _cell_text(cells[0]),
                "student_id": (
                    int(PROFILE_LINK_RE.match(student_link["href"]).group(1))
                    if student_link
                    else None
                ),
                "report_id": report_id,
                "status": status_text,
                "mark": int(mark_match.group(1)) if mark_match else None,
                "max_mark": int(mark_match.group(2)) if mark_match else None,
                "uploaded_at": _cell_text(cells[2]),
                "checked_at": _cell_text(cells[3]),
                "student_comment": _cell_text(cells[4]),
                "teacher_comment": _cell_text(cells[5]),
            }
        )
    return rows


def _parse_task_students_table(table) -> list[dict]:
    """Course students (the «п.н. / ФИО / Оценка / Загрузить отчет» table).

    The «Загрузить отчет» column carries a create link for EVERY student
    (teacher-side action), so the link only serves as the student-id source;
    it never enters the result (no report-on-behalf functionality).
    """
    rows: list[dict] = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        create_link = None
        for anchor in tr.find_all("a", href=True):
            create_match = REPORT_CREATE_RE.match(anchor["href"].split("?", 1)[0])
            if create_match:
                create_link = create_match
                break
        if create_link is None:
            continue
        name = STATUS_PARENS_RE.sub("", _cell_text(cells[1])).strip()
        rows.append({"student": name, "student_id": int(create_link.group(2))})
    return rows


def parse_group_grades(html: str) -> dict:
    """Parse the "Список группы" grade sheet (GET /inside/groups/{s}/{g}).

    One table: ФИО | one column per task ("принят (N)") | Итого ("N из M").
    """
    table = _first_table(html)
    rows = table.find_all("tr") if table is not None else []
    headers = [_cell_text(c) for c in rows[0].find_all(["th", "td"])] if rows else []
    task_columns = headers[1:-1] if len(headers) >= 3 else []

    out_rows: list[dict] = []
    for tr in rows[1:]:
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue
        marks = []
        for cell, task in zip(cells[1 : 1 + len(task_columns)], task_columns):
            text = _cell_text(cell)
            mark_match = MARK_IN_PARENS_RE.search(text)
            marks.append(
                {
                    "task": task,
                    "status": MARK_IN_PARENS_RE.sub("", text).strip() or None,
                    "mark": int(mark_match.group(1)) if mark_match else None,
                }
            )
        total_match = MARK_OF_RE.search(_cell_text(cells[-1]))
        out_rows.append(
            {
                "name": _cell_text(cells[0]),
                "marks": marks,
                "total_mark": int(total_match.group(1)) if total_match else None,
                "total_max": int(total_match.group(2)) if total_match else None,
            }
        )

    group_label = None
    if table is not None:
        group_match = re.search(r"Группа\s+(\S+)", _soup(html).get_text(" ", strip=True))
        if group_match:
            group_label = group_match.group(1)
    return {
        "group": group_label,
        "task_columns": task_columns,
        "rows": out_rows,
    }


GROUP_INFO_RE = re.compile(r"^/inside/groups/(\d+)/info$")


def parse_subject_groups(html: str, subject_id: int) -> list[dict]:
    """Groups of a subject card with their grade-sheet («Печать») links.

    The card links each group twice: /inside/groups/{gid}/info (label) and
    /inside/groups/{subject_id}/{gid} (the "Список группы" grade sheet).
    """
    soup = _soup(html)
    names: dict[int, str] = {}
    for anchor in soup.find_all("a", href=True):
        info_match = GROUP_INFO_RE.match(anchor["href"].split("?", 1)[0])
        if info_match:
            names.setdefault(
                int(info_match.group(1)), anchor.get_text(" ", strip=True)
            )

    print_re = re.compile(rf"^/inside/groups/{subject_id}/(\d+)$")
    groups: list[dict] = []
    seen: set[int] = set()
    for anchor in soup.find_all("a", href=True):
        print_match = print_re.match(anchor["href"].split("?", 1)[0])
        if print_match:
            group_id = int(print_match.group(1))
            if group_id in seen:
                continue
            seen.add(group_id)
            groups.append(
                {
                    "group_id": group_id,
                    "name": names.get(group_id),
                    "grade_sheet_url": anchor["href"].split("?", 1)[0],
                }
            )
    return sorted(groups, key=lambda g: g["name"] or "")


def parse_form_fields(html: str, action_re: re.Pattern[str]) -> dict:
    """Parse the first form whose action path matches `action_re`.

    Generic form reader for write tools (task edit, material create).
    Returns {} when the form is absent, otherwise:

        action      — form action as-is (query string included, e.g.
                      "/inside/professor/tasks/1?semesters=28&_method=PUT")
        method, enctype — form attributes (default "post"/None)
        values      — {name: str | list[str]} current values; multi-selects
                      carry lists, everything else plain strings
        checkboxes  — {name: checked}; unchecked boxes must be OMITTED from
                      the POST (Laravel treats absent as off)
        selects     — {name: {multiple, selected, options: [{value,label}]}}

        File inputs are never replayed: the caller supplies files itself.
    """
    form = None
    for candidate in _soup(html).find_all("form", action=True):
        if action_re.match(candidate["action"].split("?", 1)[0]):
            form = candidate
            break
    if form is None:
        return {}

    values: dict[str, object] = {}
    checkboxes: dict[str, bool] = {}
    selects: dict[str, dict] = {}
    for node in form.find_all(["input", "select", "textarea"]):
        name = node.get("name")
        if not name or name in values or name in checkboxes:
            continue
        if node.name == "input" and node.get("type") == "file":
            continue
        if node.name == "input" and node.get("type") == "checkbox":
            checkboxes[name] = node.get("checked") is not None
        elif node.name == "select":
            selected = [
                option.get("value", "")
                for option in node.find_all("option", selected=True)
            ]
            multiple = node.get("multiple") is not None
            selects[name] = {
                "multiple": multiple,
                "selected": selected if multiple else (selected[0] if selected else None),
                "options": [
                    {"value": o.get("value", ""), "label": _cell_text(o)}
                    for o in node.find_all("option")
                ],
            }
            values[name] = selects[name]["selected"]
        elif node.name == "textarea":
            values[name] = node.get_text("", strip=True)
        else:
            values[name] = node.get("value", "")

    return {
        "action": form["action"],
        "method": form.get("method", "post"),
        "enctype": form.get("enctype"),
        "values": values,
        "checkboxes": checkboxes,
        "selects": selects,
    }
