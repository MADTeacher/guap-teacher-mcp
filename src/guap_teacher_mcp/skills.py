"""Expose agent skills as MCP resources (Skills over MCP).

Skills are resolved from two roots, each laid out as
``<root>/<name>/SKILL.md``. The canonical root ships with the package
(packaged ``src/guap_teacher_mcp/skills`` data, falling back to the
``<repo>/skills`` layout of a repo checkout); the personal root defaults
to ``~/.agents/skills`` (``GUAP_SKILLS_DIR`` overrides the personal root
only). Canonical names define the namespace: a personal skill with the
same name replaces the canonical one whole (no merging), and personal
skills outside the canonical namespace are ignored. Resolution
(``resolve_skills``) and loading (``load_skills``) are pure functions so
they can be tested offline; ``register_skill_resources`` wires the
resolved skills into an MCPServer instance as ``skill://`` resources:

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


DEFAULT_PERSONAL_DIR = Path.home() / ".agents" / "skills"


def canonical_skills_root() -> Path:
    """Resolve the canonical skills root.

    Preferred: skills shipped inside the package (wheel install via
    pyproject force-include). Fallback: the repo checkout layout
    (<repo>/skills) so that `uv run` from the source tree keeps working.
    """
    packaged = Path(__file__).resolve().parent / "skills"
    if packaged.is_dir():
        return packaged
    # <repo>/src/guap_teacher_mcp/skills.py -> <repo>/skills
    return Path(__file__).resolve().parents[2] / "skills"


def personal_skills_root() -> Path:
    """Resolve the teacher's personal skills root; GUAP_SKILLS_DIR wins."""
    env_dir = os.environ.get(SKILLS_DIR_ENV)
    if env_dir:
        return Path(env_dir)
    return DEFAULT_PERSONAL_DIR


def resolve_skills(canonical_root: Path, personal_root: Path) -> list[Skill]:
    """Two-root resolution: canonical names define the namespace, a
    personal copy overrides by name (whole-skill, no merging); personal
    skills whose names are not in the canonical set are ignored.
    """
    canonical = {skill.name: skill for skill in load_skills(canonical_root)}
    personal = {skill.name: skill for skill in load_skills(personal_root)}
    return [personal.get(name, skill) for name, skill in sorted(canonical.items())]


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


def register_skill_resources(
    server: MCPServer, canonical_root: Path, personal_root: Path
) -> int:
    """Register resolved skills (personal overrides canonical) as skill://
    resources. Returns the number of registered skills."""
    skills = resolve_skills(canonical_root, personal_root)
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
