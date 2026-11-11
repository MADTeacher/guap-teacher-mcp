"""Offline tests for the guap-teacher CLI (init / skills diff / protocol)."""

import json
from pathlib import Path

import pytest

from guap_teacher_mcp import skills as skills_mod
from guap_teacher_mcp.cli import main


def _make_skill(root: Path, name: str, markdown: str = "# canon") -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(markdown, encoding="utf-8")


def test_init_seeds_and_prints_snippets(tmp_path, capsys, monkeypatch):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-review", "# Review canon")
    monkeypatch.setattr(skills_mod, "canonical_skills_root", lambda: canon)

    rc = main(["init", "--skills-dir", str(personal)])

    assert rc == 0
    seeded = (personal / "guap-review" / "SKILL.md").read_text(encoding="utf-8")
    assert seeded == "# Review canon"
    out = capsys.readouterr().out
    assert "guap-review" in out
    assert "mcpServers" in out          # MCP config snippets printed
    assert str(personal) in out         # personal dir reported


def test_init_keeps_existing_personal_copy(tmp_path, capsys, monkeypatch):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-review", "# NEW canon")
    _make_skill(personal, "guap-review", "# MY vision")
    monkeypatch.setattr(skills_mod, "canonical_skills_root", lambda: canon)

    rc = main(["init", "--skills-dir", str(personal)])

    assert rc == 0
    assert (personal / "guap-review" / "SKILL.md").read_text(encoding="utf-8") == "# MY vision"
    assert "не перезаписаны" in capsys.readouterr().out


def test_skills_diff_prints_statuses(tmp_path, capsys, monkeypatch):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-a", "# same")
    _make_skill(canon, "guap-b", "# canon b")
    _make_skill(canon, "guap-c", "# canon c")
    _make_skill(personal, "guap-a", "# same")
    _make_skill(personal, "guap-b", "# my b")
    monkeypatch.setattr(skills_mod, "canonical_skills_root", lambda: canon)

    rc = main(["skills", "diff", "--skills-dir", str(personal)])

    assert rc == 0
    out = capsys.readouterr().out
    assert "guap-a: identical" in out
    assert "guap-b: differs" in out
    assert "guap-c: missing" in out


def test_empty_skills_dir_is_rejected(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["init", "--skills-dir", ""])
    assert exc.value.code == 2


def test_protocol_subcommand_roundtrip(tmp_path, capsys):
    xlsx = tmp_path / "Протокол.xlsx"
    payload = tmp_path / "records.json"
    payload.write_text(
        json.dumps(
            {
                "date": "2026-11-11",
                "subject": "Основы разработки на Dart",
                "group": "4613МК",
                "student": "Иванов И. И.",
                "task": "Практическая №5",
                "report_id": 101,
                "max_mark": 10,
                "proposed_mark": 8,
            }
        ),
        encoding="utf-8",
    )

    assert main(["protocol", "append", str(xlsx), str(payload)]) == 0
    assert "appended 1 row(s)" in capsys.readouterr().out
    assert xlsx.exists()

    assert main(["protocol", "pending", str(xlsx)]) == 0
    pending = json.loads(capsys.readouterr().out)
    assert [r["report_id"] for r in pending] == [101]

    assert main(["protocol", "posted", str(xlsx), "101", "--mark", "8"]) == 0
    posted = json.loads(capsys.readouterr().out)
    assert posted["portal_status"].startswith("выставлен")

    assert main(["protocol", "pending", str(xlsx)]) == 0
    assert json.loads(capsys.readouterr().out) == []
