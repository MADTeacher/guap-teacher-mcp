"""Offline tests for the pure helpers of the write tools in server.py."""

from guap_teacher_mcp.server import _normalize_notice_datetime


def test_normalize_notice_datetime_iso_passthrough() -> None:
    assert _normalize_notice_datetime("2026-11-10T15:31") == "2026-11-10T15:31"


def test_normalize_notice_datetime_ru_to_iso() -> None:
    assert _normalize_notice_datetime("10.11.2026 09:05") == "2026-11-10T09:05"
    assert _normalize_notice_datetime("01.02.2027 23:59") == "2027-02-01T23:59"


def test_normalize_notice_datetime_clears_with_empty_string() -> None:
    assert _normalize_notice_datetime("") == ""
    assert _normalize_notice_datetime("   ") == ""


def test_normalize_notice_datetime_rejects_garbage() -> None:
    assert _normalize_notice_datetime("10.11.2026") is None  # no time part
    assert _normalize_notice_datetime("2026-11-10 15:31") is None  # space, not T
    assert _normalize_notice_datetime("мусор") is None
