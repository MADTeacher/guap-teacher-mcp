"""Offline tests for skills.py (Skills over MCP resource registration)."""

from pathlib import Path

import pytest
from mcp.server.mcpserver import MCPServer

from guap_teacher_mcp.skills import load_skills, register_skill_resources

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


@pytest.mark.asyncio
async def test_register_skill_resources_exposes_skill_uris(tmp_path):
    _make_skill(tmp_path, "alpha", "# Alpha")
    _make_skill(tmp_path, "beta", "# Beta")
    server = MCPServer("test-skills")

    assert register_skill_resources(server, tmp_path) == 2

    resources = await server.list_resources()
    uris = {str(r.uri) for r in resources}
    assert {"skill://index", "skill://alpha", "skill://beta"} <= uris

    index = await server.read_resource("skill://index")
    assert "skill://alpha" in index[0].content

    alpha = await server.read_resource("skill://alpha")
    assert alpha[0].content == "# Alpha"


@pytest.mark.asyncio
async def test_register_skill_resources_empty_dir_is_noop(tmp_path):
    server = MCPServer("test-skills-empty")
    assert register_skill_resources(server, tmp_path / "nope") == 0
    assert await server.list_resources() == []
