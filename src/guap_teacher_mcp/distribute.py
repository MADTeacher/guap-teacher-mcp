"""Seeding and diffing the teacher's personal skill copies.

Pure offline functions on two roots: canonical skills (shipped with the
package) and the personal directory (``~/.agents/skills`` by default).
Seeding never overwrites existing files — the teacher's vision is sacred.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from guap_teacher_mcp.skills import SKILL_FILE, load_skills


@dataclass(frozen=True)
class SeedResult:
    """Outcome of seeding: newly installed and skipped (kept) skill names."""

    seeded: list[str]
    skipped: list[str]


def seed_personal_skills(canonical_root: Path, personal_root: Path) -> SeedResult:
    """Copy canonical ``<name>/SKILL.md`` into ``personal_root``.

    Existing personal files are never overwritten (idempotent; re-runs
    install only skills that are missing, including newly added canonical
    ones). Canonical skills are single-file today, so only SKILL.md is
    copied.
    """
    seeded: list[str] = []
    skipped: list[str] = []
    for skill in load_skills(canonical_root):
        target = personal_root / skill.name / SKILL_FILE
        if target.exists():
            skipped.append(skill.name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(skill.markdown, encoding="utf-8")
        seeded.append(skill.name)
    return SeedResult(seeded=sorted(seeded), skipped=sorted(skipped))


@dataclass(frozen=True)
class SkillDiff:
    """Comparison of one canonical skill against the personal copy."""

    name: str
    status: str  # "identical" | "differs" | "missing"


def diff_personal_skills(canonical_root: Path, personal_root: Path) -> list[SkillDiff]:
    """Compare personal copies with canonical skills, read-only.

    ``differs`` is the normal state of a customized skill; ``missing``
    means a canonical skill absent from the personal directory (a re-run
    of ``guap-teacher init`` would install it). No merging is ever done.
    """
    canonical = {skill.name: skill.markdown for skill in load_skills(canonical_root)}
    personal = {skill.name: skill.markdown for skill in load_skills(personal_root)}
    result: list[SkillDiff] = []
    for name in sorted(canonical):
        if name not in personal:
            status = "missing"
        elif personal[name] == canonical[name]:
            status = "identical"
        else:
            status = "differs"
        result.append(SkillDiff(name=name, status=status))
    return result
