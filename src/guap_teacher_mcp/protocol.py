"""Review protocol journal: an .xlsx workbook per discipline accumulating
review records (remarks, understanding-check questions, marks) and tracking
which marks have already been posted to pro.guap.ru.

The journal is self-sufficient for grading in any agent session, including
a fresh one: every row carries the portal ``report_id``, the discipline,
the task, both marks and the posting status. Pure offline functions over
openpyxl plus a small CLI used by the guap-review skill:

- ``append <xlsx> <json>``  - append review record(s) (creates the file);
- ``pending <xlsx>``        - rows whose mark is not posted to the portal yet;
- ``posted <xlsx> <id>``    - mark a report_id as posted (records final mark).

The journal holds personal data of students: it lives outside the repo,
is never committed and never leaves the teacher's machine.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

SHEET = "Протокол"
DEFAULT_PORTAL_STATUS = "не выставлено"
POSTED_PREFIX = "выставлен"

# (header, record field, column width, wrap text) — single source of layout.
COLUMNS: list[tuple[str, str, float, bool]] = [
    ("Дата проверки", "date", 12, False),
    ("Дисциплина", "subject", 20, False),
    ("Группа", "group", 10, False),
    ("Студент", "student", 22, False),
    ("Задание", "task", 28, False),
    ("report_id", "report_id", 10, False),
    ("Макс. балл", "max_mark", 10, False),
    ("Претензии", "complaints", 11, False),
    ("Замечания", "remarks", 45, True),
    ("Вопросы на понимание", "questions", 60, True),
    ("Балл (предв.)", "proposed_mark", 11, False),
    ("Балл (итог)", "final_mark", 11, False),
    ("Портал", "portal_status", 20, False),
]


def _question_lines(questions: object) -> str:
    """Render questions: a list gets numbered, a plain string passes through."""
    if questions in (None, ""):
        return ""
    if isinstance(questions, str):
        return questions
    return "\n".join(f"{i}) {q}" for i, q in enumerate(questions, 1))


def _cell_value(record: dict, field: str) -> object:
    """Map a record field to its cell value (with sane defaults)."""
    if field == "questions":
        return _question_lines(record.get(field))
    if field == "portal_status":
        return record.get(field) or DEFAULT_PORTAL_STATUS
    return record.get(field, "")


def _header_map(ws) -> dict[str, int]:
    """Header name -> 1-based column index from row 1 of the sheet."""
    return {str(cell.value): cell.column for cell in ws[1] if cell.value}


def _open_sheet(path: Path):
    """Open (or create) the journal workbook and its protocol sheet."""
    if path.exists():
        wb = load_workbook(path)
        ws = wb[SHEET] if SHEET in wb.sheetnames else wb.active
        missing = [h for h, _, _, _ in COLUMNS if h not in _header_map(ws)]
        if missing:
            raise ValueError(
                f"{path}: columns missing from the header: {', '.join(missing)}"
            )
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = SHEET
        for col, (header, _, width, _) in enumerate(COLUMNS, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            ws.column_dimensions[get_column_letter(col)].width = width
        ws.freeze_panes = "A2"
        path.parent.mkdir(parents=True, exist_ok=True)
    return wb, ws


def append_records(records: dict | list[dict], path: str | Path) -> list[int]:
    """Append review record(s) to the journal; returns 1-based row numbers."""
    path = Path(path)
    items = records if isinstance(records, list) else [records]
    wb, ws = _open_sheet(path)
    hmap = _header_map(ws)
    written: list[int] = []
    for record in items:
        row = ws.max_row + 1
        for header, field, _, wrap in COLUMNS:
            cell = ws.cell(row=row, column=hmap[header], value=_cell_value(record, field))
            if wrap:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        written.append(row)
    wb.save(path)
    return written


def read_rows(path: str | Path) -> list[dict]:
    """All journal rows as record dicts (plus their sheet row number)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"journal not found: {path}")
    wb = load_workbook(path, data_only=True)
    ws = wb[SHEET] if SHEET in wb.sheetnames else wb.active
    hmap = _header_map(ws)
    rows: list[dict] = []
    for r in range(2, ws.max_row + 1):
        record = {
            field: ws.cell(row=r, column=hmap[header]).value
            for header, field, _, _ in COLUMNS
            if header in hmap
        }
        if any(value not in (None, "") for value in record.values()):
            record["row"] = r
            rows.append(record)
    return rows


def pending_rows(path: str | Path) -> list[dict]:
    """Rows whose mark (final, else proposed) is not posted to the portal.

    Deduplicated by report_id: a report reviewed several times (resubmits)
    appears once, its latest review winning.
    """
    by_report: dict[str, dict] = {}
    for row in read_rows(path):
        status = str(row.get("portal_status") or "")
        if status.startswith(POSTED_PREFIX):
            by_report.pop(str(row.get("report_id")), None)
            continue
        mark = row.get("final_mark")
        if mark in (None, ""):
            mark = row.get("proposed_mark")
        if mark in (None, ""):
            by_report.pop(str(row.get("report_id")), None)
            continue
        by_report[str(row.get("report_id"))] = {**row, "mark": mark}
    return list(by_report.values())


def mark_posted(
    path: str | Path,
    report_id: int | str,
    mark: int | None = None,
    date: str | None = None,
) -> dict:
    """Flag every row of ``report_id`` as posted; returns the latest row.

    The portal state is per report (not per review), so a posted mark closes
    all reviews of that report; the final mark lands on the latest row.
    """
    path = Path(path)
    matches = [
        r
        for r in read_rows(path)
        if str(r.get("report_id")).strip() == str(report_id).strip()
    ]
    if not matches:
        raise KeyError(f"report_id {report_id} not found in {path}")
    day = date or datetime.date.today().isoformat()
    wb = load_workbook(path)
    ws = wb[SHEET] if SHEET in wb.sheetnames else wb.active
    hmap = _header_map(ws)
    for row in matches:
        ws.cell(row=row["row"], column=hmap["Портал"], value=f"{POSTED_PREFIX} {day}")
    latest = matches[-1]
    if mark is not None:
        ws.cell(row=latest["row"], column=hmap["Балл (итог)"], value=mark)
    wb.save(path)
    row = dict(latest)
    if mark is not None:
        row["final_mark"] = mark
    row["portal_status"] = f"{POSTED_PREFIX} {day}"
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="guap-teacher-protocol",
        description="Review protocol journal (.xlsx) for the guap-review skill.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append", help="append review record(s) from JSON")
    p_append.add_argument("xlsx")
    p_append.add_argument("json")

    p_pending = sub.add_parser("pending", help="rows whose mark is not posted yet")
    p_pending.add_argument("xlsx")

    p_posted = sub.add_parser("posted", help="mark report_id as posted to the portal")
    p_posted.add_argument("xlsx")
    p_posted.add_argument("report_id")
    p_posted.add_argument("--mark", type=int, default=None, help="final mark to record")
    p_posted.add_argument("--date", default=None, help="posting date, YYYY-MM-DD")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "append":
            records = json.loads(Path(args.json).read_text(encoding="utf-8"))
            rows = append_records(records, args.xlsx)
            print(f"appended {len(rows)} row(s) -> {args.xlsx}")
        elif args.cmd == "pending":
            print(json.dumps(pending_rows(args.xlsx), ensure_ascii=False, indent=2))
        else:
            row = mark_posted(args.xlsx, args.report_id, mark=args.mark, date=args.date)
            print(json.dumps(row, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
