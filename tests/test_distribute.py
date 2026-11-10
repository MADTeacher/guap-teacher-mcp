"""Offline tests for distribute.py (seeding personal skill copies)."""

from pathlib import Path

from guap_teacher_mcp.distribute import diff_personal_skills, seed_personal_skills


def _make_skill(root: Path, name: str, markdown: str = "# skill") -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(markdown, encoding="utf-8")


def test_seed_installs_missing_skills(tmp_path):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-review", "# Review canon")
    _make_skill(canon, "guap-schedule", "# Schedule canon")

    result = seed_personal_skills(canon, personal)

    assert result.seeded == ["guap-review", "guap-schedule"]
    assert result.skipped == []
    assert (personal / "guap-review" / "SKILL.md").read_text(encoding="utf-8") == "# Review canon"


def test_seed_never_overwrites_existing(tmp_path):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-review", "# NEW canon")
    _make_skill(personal, "guap-review", "# MY vision")

    result = seed_personal_skills(canon, personal)

    assert result.seeded == []
    assert result.skipped == ["guap-review"]
    assert (personal / "guap-review" / "SKILL.md").read_text(encoding="utf-8") == "# MY vision"


def test_seed_is_idempotent(tmp_path):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-review", "# canon")
    first = seed_personal_skills(canon, personal)
    second = seed_personal_skills(canon, personal)
    assert first.seeded == ["guap-review"]
    assert second.seeded == [] and second.skipped == ["guap-review"]


def test_seed_empty_canonical_is_noop(tmp_path):
    canon = tmp_path / "canon"
    canon.mkdir()
    result = seed_personal_skills(canon, tmp_path / "personal")
    assert result.seeded == [] and result.skipped == []


def test_diff_statuses(tmp_path):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-a", "# same")
    _make_skill(canon, "guap-b", "# canon b")
    _make_skill(canon, "guap-c", "# canon c")
    _make_skill(personal, "guap-a", "# same")   # identical
    _make_skill(personal, "guap-b", "# my b")   # differs
    # guap-c intentionally missing from personal

    diffs = diff_personal_skills(canon, personal)

    assert [(d.name, d.status) for d in diffs] == [
        ("guap-a", "identical"),
        ("guap-b", "differs"),
        ("guap-c", "missing"),
    ]


def test_diff_missing_personal_dir_all_missing(tmp_path):
    canon = tmp_path / "canon"
    _make_skill(canon, "guap-a", "# a")
    diffs = diff_personal_skills(canon, tmp_path / "nope")
    assert [(d.name, d.status) for d in diffs] == [("guap-a", "missing")]
