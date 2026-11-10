"""Expose repository skills as MCP resources (Skills over MCP).

Skills live as ``skills/<name>/SKILL.md`` in the repository root (one
subdirectory per skill). The loader is a pure function so it can be tested
offline; ``register_skill_resources`` wires the loaded skills into an
MCPServer instance as ``skill://`` resources:

- ``skill://index`` — catalog of the available skills;
- ``skill://<name>`` — the SKILL.md content of the skill (text/markdown).

The name ``index`` is reserved for the catalog. Note that ZCode itself does
not (yet) discover skills over MCP — for ZCode availability a thin stub is
kept in ``.zcode/skills/<name>/SKILL.md`` pointing here; the server-side
resources serve any MCP client that speaks `resources/list`/`resources/read`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from mcp.server.mcpserver import MCPServer

SKILL_FILE = "SKILL.md"
SKILLS_DIR_ENV = "GUAP_SKILLS_DIR"


@dataclass(frozen=True)
class Skill:
    """A single agent skill: directory name plus SKILL.md content."""

    name: str
    markdown: str


def skills_root() -> Path:
    """Resolve the skills directory; GUAP_SKILLS_DIR env override wins."""
    env_dir = os.environ.get(SKILLS_DIR_ENV)
    if env_dir:
        return Path(env_dir)
    # <repo>/src/guap_teacher_mcp/skills.py -> <repo>/skills
    return Path(__file__).resolve().parents[2] / "skills"


def load_skills(root: Path) -> list[Skill]:
    """Load skills from ``root/<name>/SKILL.md``, sorted by name.

    Pure offline function: a missing directory or a subdirectory without
    SKILL.md is simply skipped (empty list / no entry).
    """
    if not root.is_dir():
        return []
    return [
        Skill(name=path.parent.name, markdown=path.read_text(encoding="utf-8"))
        for path in sorted(root.glob(f"*/{SKILL_FILE}"))
    ]


def register_skill_resources(server: MCPServer, root: Path) -> int:
    """Register the skills of ``root`` on ``server`` as skill:// resources.

    Returns the number of registered skills (0 = nothing registered, e.g.
    the directory does not exist).
    """
    skills = load_skills(root)
    if not skills:
        return 0
    names = [skill.name for skill in skills]

    @server.resource(
        "skill://index",
        name="skills-index",
        description="Каталог агентских навыков guap-teacher (skill://<имя>)",
        mime_type="text/markdown",
    )
    def _index() -> str:
        lines = ["# Навыки guap-teacher", ""]
        lines += [f"- skill://{name} — агентский навык «{name}»" for name in names]
        return "\n".join(lines)

    def _register(skill: Skill) -> None:
        # A factory keeps a per-skill closure (no late binding of the loop
        # variable); the reader function must take no parameters because
        # the URI is static.
        @server.resource(
            f"skill://{skill.name}",
            name=f"skill-{skill.name}",
            description=f"Агентский навык {skill.name} (SKILL.md)",
            mime_type="text/markdown",
        )
        def _skill() -> str:
            return skill.markdown

    for skill in skills:
        _register(skill)
    return len(skills)
