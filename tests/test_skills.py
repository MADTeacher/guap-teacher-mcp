"""Offline tests for skills.py (Skills over MCP resource registration)."""

from pathlib import Path

import pytest
from mcp.server.mcpserver import MCPServer

from guap_teacher_mcp.skills import (
    canonical_skills_root,
    load_skills,
    personal_skills_root,
    register_skill_resources,
    resolve_skills,
)

REPO_SKILLS = Path(__file__).resolve().parents[1] / "skills"


def _make_skill(root: Path, name: str, markdown: str = "# skill") -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(markdown, encoding="utf-8")


def test_load_skills_reads_names_sorted(tmp_path):
    _make_skill(tmp_path, "beta", "# Beta")
    _make_skill(tmp_path, "alpha", "# Alpha")
    skills = load_skills(tmp_path)
    assert [s.name for s in skills] == ["alpha", "beta"]
    assert skills[0].markdown == "# Alpha"


def test_load_skills_missing_dir_returns_empty(tmp_path):
    assert load_skills(tmp_path / "nope") == []


def test_load_skills_skips_dirs_without_skill_file(tmp_path):
    _make_skill(tmp_path, "alpha")
    (tmp_path / "not-a-skill").mkdir()
    skills = load_skills(tmp_path)
    assert [s.name for s in skills] == ["alpha"]


def test_load_skills_repo_canonical_guap_schedule():
    """The canonical repo skill must load with valid frontmatter."""
    skills = load_skills(REPO_SKILLS)
    names = [s.name for s in skills]
    assert "guap-schedule" in names
    markdown = next(s.markdown for s in skills if s.name == "guap-schedule")
    assert markdown.startswith("---")
    assert "name: guap-schedule" in markdown


def test_resolve_skills_personal_overrides_and_filters(tmp_path):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "guap-a", "# canon a")
    _make_skill(canon, "guap-b", "# canon b")
    _make_skill(personal, "guap-b", "# my b")          # personal override
    _make_skill(personal, "other-tool", "# foreign")   # not in canon -> ignored
    resolved = resolve_skills(canon, personal)
    assert [(s.name, s.markdown) for s in resolved] == [
        ("guap-a", "# canon a"),
        ("guap-b", "# my b"),
    ]


def test_resolve_skills_missing_personal_returns_canonical(tmp_path):
    canon = tmp_path / "canon"
    _make_skill(canon, "guap-a", "# a")
    resolved = resolve_skills(canon, tmp_path / "nope")
    assert [(s.name, s.markdown) for s in resolved] == [("guap-a", "# a")]


def test_canonical_skills_root_works_from_repo_checkout():
    root = canonical_skills_root()
    assert (root / "guap-review" / "SKILL.md").is_file()


def test_personal_skills_root_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("GUAP_SKILLS_DIR", str(tmp_path))
    assert personal_skills_root() == tmp_path


def test_personal_skills_root_default_is_agents_dir(monkeypatch):
    monkeypatch.delenv("GUAP_SKILLS_DIR", raising=False)
    assert personal_skills_root() == Path.home() / ".agents" / "skills"


@pytest.mark.asyncio
async def test_register_skill_resources_exposes_skill_uris(tmp_path):
    canon, personal = tmp_path / "canon", tmp_path / "personal"
    _make_skill(canon, "alpha", "# Alpha")
    _make_skill(canon, "beta", "# Beta")
    _make_skill(personal, "beta", "# My Beta")      # personal wins
    _make_skill(personal, "foreign", "# Not guap")  # ignored: not in canon
    server = MCPServer("test-skills")

    assert register_skill_resources(server, canon, personal) == 2

    resources = await server.list_resources()
    uris = {str(r.uri) for r in resources}
    assert {"skill://index", "skill://alpha", "skill://beta"} <= uris
    assert "skill://foreign" not in uris

    beta = await server.read_resource("skill://beta")
    assert "My Beta" in beta[0].content


@pytest.mark.asyncio
async def test_register_skill_resources_empty_dir_is_noop(tmp_path):
    server = MCPServer("test-skills-empty")
    assert register_skill_resources(server, tmp_path / "nope", tmp_path / "nope2") == 0
    assert await server.list_resources() == []


def test_canonical_skills_document_customization_section():
    """Every canonical skill must explain where the personal copy lives."""
    for skill in load_skills(REPO_SKILLS):
        assert "## Настройка под себя" in skill.markdown, skill.name
        assert "~/.agents/skills" in skill.markdown, skill.name
        assert "guap-teacher skills diff" in skill.markdown, skill.name
