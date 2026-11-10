"""Offline tests for protocol.py (review protocol journal)."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from guap_teacher_mcp.protocol import (
    DEFAULT_PORTAL_STATUS,
    SHEET,
    append_records,
    mark_posted,
    pending_rows,
    read_rows,
)


def _record(report_id: int, **overrides) -> dict:
    record = {
        "date": "2026-11-10",
        "subject": "Основы разработки на Dart",
        "group": "4613МК",
        "student": "Иванов И. И.",
        "task": "ЛР №3 «Циклы»",
        "report_id": report_id,
        "max_mark": 10,
        "complaints": "есть",
        "remarks": "листинг 2 (с. 5): «умные» кавычки, не компилируется",
        "questions": [
            "с. 5, листинг 2 — почему выбран while, а не for?",
            "что произойдёт при пустом списке?",
            "откуда константа 0.001?",
        ],
        "proposed_mark": 8,
    }
    record.update(overrides)
    return record


def test_append_creates_journal_with_header(tmp_path):
    xlsx = tmp_path / "Протокол.xlsx"
    rows = append_records(_record(101), xlsx)

    assert rows == [2]
    ws = load_workbook(xlsx)[SHEET]
    assert ws.freeze_panes == "A2"
    assert ws.cell(row=1, column=1).value == "Дата проверки"
    assert ws.cell(row=1, column=13).value == "Портал"
    assert ws.cell(row=1, column=1).font.bold

    data = read_rows(xlsx)
    assert len(data) == 1
    row = data[0]
    assert row["student"] == "Иванов И. И."
    assert row["report_id"] == 101
    assert row["portal_status"] == DEFAULT_PORTAL_STATUS
    assert "1) с. 5, листинг 2" in row["questions"]
    assert "3) откуда константа 0.001?" in row["questions"]


def test_append_accepts_batch_and_plain_string_questions(tmp_path):
    xlsx = tmp_path / "Протокол.xlsx"
    rows = append_records(
        [_record(101), _record(102, questions="один общий вопрос")], xlsx
    )
    assert rows == [2, 3]
    data = read_rows(xlsx)
    assert len(data) == 2
    assert data[1]["questions"] == "один общий вопрос"


def test_append_twice_keeps_header_and_grows(tmp_path):
    xlsx = tmp_path / "Протокол.xlsx"
    append_records(_record(101), xlsx)
    append_records(_record(102, student="Петров П. П.", proposed_mark=10), xlsx)
    ws = load_workbook(xlsx)[SHEET]
    assert ws.max_row == 3  # header + 2 records
    assert ws.cell(row=1, column=1).value == "Дата проверки"


def test_pending_returns_unposted_marks(tmp_path):
    xlsx = tmp_path / "Протокол.xlsx"
    append_records(
        [
            _record(101, proposed_mark=8),
            _record(102, proposed_mark=9, final_mark=7),
            _record(103, proposed_mark=""),  # no mark yet -> not pending
        ],
        xlsx,
    )
    pending = pending_rows(xlsx)
    assert [r["report_id"] for r in pending] == [101, 102]
    assert pending[0]["mark"] == 8
    assert pending[1]["mark"] == 7  # final wins over proposed


def test_mark_posted_flags_latest_row(tmp_path):
    xlsx = tmp_path / "Протокол.xlsx"
    append_records([_record(101, proposed_mark=6), _record(102)], xlsx)
    # a resubmission: same report reviewed again, higher mark
    append_records(_record(101, proposed_mark=8, remarks="исправлено"), xlsx)

    row = mark_posted(xlsx, 101, mark=8, date="2026-11-12")
    assert row["final_mark"] == 8
    assert row["portal_status"] == "выставлен 2026-11-12"

    pending = pending_rows(xlsx)
    assert [r["report_id"] for r in pending] == [102]
    data = read_rows(xlsx)
    # a posted report closes all its review rows, not just the latest
    assert data[0]["portal_status"] == "выставлен 2026-11-12"
    assert data[2]["portal_status"] == "выставлен 2026-11-12"
    assert data[1]["portal_status"] == DEFAULT_PORTAL_STATUS


def test_pending_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_rows(tmp_path / "nope.xlsx")


def test_mark_posted_unknown_report_id(tmp_path):
    xlsx = tmp_path / "Протокол.xlsx"
    append_records(_record(101), xlsx)
    with pytest.raises(KeyError):
        mark_posted(xlsx, 999)
