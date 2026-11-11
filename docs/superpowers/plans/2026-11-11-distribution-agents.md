# Распространение guap-teacher через ~/.agents/skills — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Преподаватель ставит движок одной uvx-командой (`init`), получает личные копии навыков в `~/.agents/skills/` (ZCode/Codex/Qwen читают нативно), правит их свободно; движок обновляется, не задевая личные копии; `skills diff` показывает отличия от канона.

**Architecture:** Два слоя: движок (uv-пакет; канонические навыки едут в wheel как package data) и личный каталог `~/.agents/skills/guap-*` (единственное место методологии). Загрузчик сервера разрешает навыки из двух корней: личный побеждает при совпадении имени, не-канонические имена из личного каталога игнорируются. CLI получает подкоманды `init` и `skills diff`; без аргументов — прежний старт MCP-сервера (stdio), действующие MCP-конфиги не меняются.

**Tech Stack:** Python 3.12, stdlib `argparse`, hatchling (package data через force-include), pytest (только офлайн). Новых зависимостей нет.

**Spec:** `docs/superpowers/specs/2026-11-11-distribution-agents-design.md`

**Вне scope этого плана:** плагин ZCode (фаза 2, отдельный репозиторий `C:\Users\MADTeacher\Documents\GitHub\guap-teacher-plugin`), публикация на PyPI, поддержка Claude Code.

## Global Constraints

- Менеджер пакетов — только uv; новых зависимостей не добавлять.
- Python 3.12 (зафиксирован в `.python-version`).
- Тесты — только офлайн, без сети (правило AGENTS.md); tmp-каталоги через `tmp_path`.
- Идентификаторы и комментарии — английские; docstring'и MCP-инструментов и пользовательский вывод CLI — русские.
- Build-backend — hatchling; пакеты в wheel: `src/guap_teacher_mcp`.
- Перед каждым коммитом: затронутые тесты зелёные; в конце — `uv run pytest` целиком зелёный и `uv run python -c "import guap_teacher_mcp.server"` без ошибок.
- URL публикации `git+https://github.com/MADTeacher/guap-teacher-mcp` подставлен при публикации (в спеке это был открытый пункт с `<owner>`). Значение живёт в одной константе `PACKAGE_SOURCE` в `cli.py`; в README-тексте задачи то же правило.

---

### Task 1: Двухкорневое разрешение навыков в `skills.py`

**Files:**
- Modify: `src/guap_teacher_mcp/skills.py` (заменить `skills_root()` на `canonical_skills_root()` + `personal_skills_root()`; добавить `resolve_skills()`; поменять сигнатуру `register_skill_resources`)
- Modify: `src/guap_teacher_mcp/server.py` (строка вызова `register_skill_resources` в конце файла)
- Modify: `tests/test_skills.py` (обновить тест регистрации под новую сигнатуру; добавить тесты разрешения)

**Interfaces:**
- Consumes: существующие `load_skills(root) -> list[Skill]`, `Skill(name, markdown)`, константа `SKILLS_DIR_ENV = "GUAP_SKILLS_DIR"`.
- Produces (используют Task 2–4):
  - `canonical_skills_root() -> Path` ( packaged `src/guap_teacher_mcp/skills` если есть, иначе `<repo>/skills`)
  - `personal_skills_root() -> Path` (`GUAP_SKILLS_DIR` env, иначе `~/.agents/skills`)
  - `resolve_skills(canonical_root: Path, personal_root: Path) -> list[Skill]`
  - `register_skill_resources(server: MCPServer, canonical_root: Path, personal_root: Path) -> int`

- [ ] **Step 1: Write the failing tests**

В `tests/test_skills.py` обновить импорт и добавить тесты (в существующем файле уже есть хелпер `_make_skill` и константа `REPO_SKILLS`):

```python
# импорт в шапке файла дополнить:
from guap_teacher_mcp.skills import (
    canonical_skills_root,
    load_skills,
    personal_skills_root,
    register_skill_resources,
    resolve_skills,
)
```

```python
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
```

Заменить существующий `test_register_skill_resources_exposes_skill_uris` (новая сигнатура + семантика переопределения):

```python
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
```

(Если обращение к содержимому ресурса в старой версии теста отличалось — свериться с ней; mcp SDK возвращает список `ReadResourceContents` с полем `.content`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_skills.py -v`
Expected: FAIL — `ImportError: cannot import name 'canonical_skills_root'` (и `resolve_skills`).

- [ ] **Step 3: Implement in `skills.py`**

Удалить функцию `skills_root()` и заменить блоком (модульный docstring обновить: личный каталог по умолчанию `~/.agents/skills`, канон — package data; `GUAP_SKILLS_DIR` теперь переопределяет личный корень):

```python
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
```

Сигнатура и первая строка `register_skill_resources`:

```python
def register_skill_resources(
    server: MCPServer, canonical_root: Path, personal_root: Path
) -> int:
    """Register resolved skills (personal overrides canonical) as skill://
    resources. Returns the number of registered skills."""
    skills = resolve_skills(canonical_root, personal_root)
```

(тело функции после этой строки не меняется).

- [ ] **Step 4: Update the call site in `server.py`**

В конце `src/guap_teacher_mcp/server.py` заменить:

```python
register_skill_resources(mcp, skills_root())
```

на (импорт `skills` — модульный, если сейчас импортируются отдельные имена — заменить на `from guap_teacher_mcp import skills`):

```python
register_skill_resources(
    mcp, skills.canonical_skills_root(), skills.personal_skills_root()
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_skills.py -v`
Expected: PASS (все, включая старые `test_load_skills_*`).

- [ ] **Step 6: Commit**

```bash
git add src/guap_teacher_mcp/skills.py src/guap_teacher_mcp/server.py tests/test_skills.py
git commit -m "feat: two-root skill resolution (personal ~/.agents/skills overrides canonical)"
```

---

### Task 2: Посев личных копий — `seed_personal_skills`

**Files:**
- Create: `src/guap_teacher_mcp/distribute.py`
- Create: `tests/test_distribute.py`

**Interfaces:**
- Consumes: `skills.load_skills(root) -> list[Skill]`, `skills.SKILL_FILE` (переиспользовать константу: `from guap_teacher_mcp.skills import SKILL_FILE, load_skills`).
- Produces (использует Task 4 CLI):
  - `@dataclass(frozen=True) class SeedResult` с полями `seeded: list[str]`, `skipped: list[str]` (отсортированные имена)
  - `seed_personal_skills(canonical_root: Path, personal_root: Path) -> SeedResult` — копирует `SKILL.md` каждого канонического навыка в `personal_root/<имя>/SKILL.md`; существующие не перезаписывает никогда; каталоги создаёт.

- [ ] **Step 1: Write the failing tests**

`tests/test_distribute.py`:

```python
"""Offline tests for distribute.py (seeding personal skill copies)."""

from pathlib import Path

from guap_teacher_mcp.distribute import seed_personal_skills


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_distribute.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'guap_teacher_mcp.distribute'`.

- [ ] **Step 3: Implement `distribute.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_distribute.py -v`
Expected: PASS (4 теста).

- [ ] **Step 5: Commit**

```bash
git add src/guap_teacher_mcp/distribute.py tests/test_distribute.py
git commit -m "feat: seed_personal_skills — install missing personal copies, never overwrite"
```

---

### Task 3: Сравнение с каноном — `diff_personal_skills`

**Files:**
- Modify: `src/guap_teacher_mcp/distribute.py`
- Modify: `tests/test_distribute.py`

**Interfaces:**
- Consumes: `skills.load_skills`.
- Produces (использует Task 4 CLI):
  - `@dataclass(frozen=True) class SkillDiff` с полями `name: str`, `status: str` (`"identical"` | `"differs"` | `"missing"`)
  - `diff_personal_skills(canonical_root: Path, personal_root: Path) -> list[SkillDiff]` — по каждому каноническому имени, отсортировано по имени.

- [ ] **Step 1: Write the failing tests**

Добавить в `tests/test_distribute.py`:

```python
from guap_teacher_mcp.distribute import diff_personal_skills  # дополнить импорт


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_distribute.py -v`
Expected: FAIL — `ImportError: cannot import name 'diff_personal_skills'`.

- [ ] **Step 3: Implement**

Добавить в `distribute.py` (после `SeedResult`/`seed_personal_skills`):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_distribute.py -v`
Expected: PASS (6 тестов).

- [ ] **Step 5: Commit**

```bash
git add src/guap_teacher_mcp/distribute.py tests/test_distribute.py
git commit -m "feat: diff_personal_skills — read-only personal vs canonical comparison"
```

---

### Task 4: CLI — подкоманды `init` и `skills diff`

**Files:**
- Create: `src/guap_teacher_mcp/cli.py`
- Modify: `pyproject.toml` (`[project.scripts]` → `guap_teacher_mcp.cli:main`)
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `skills.canonical_skills_root()`, `skills.personal_skills_root()` (вызывать как `skills.<имя>` — monkeypatch-ируемо в тестах), `distribute.seed_personal_skills`, `distribute.diff_personal_skills`, `server.main` (ленивый импорт только для старта сервера).
- Produces: `main(argv: list[str] | None = None) -> int` (0 — успех); console script `guap-teacher`: без аргументов — прежний stdio-сервер; `init [--skills-dir <path>]`; `skills diff [--skills-dir <path>]`; `skills` без подкоманды — ошибка argparse.

- [ ] **Step 1: Write the failing tests**

`tests/test_cli.py`:

```python
"""Offline tests for the guap-teacher CLI (init / skills diff)."""

from pathlib import Path

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'guap_teacher_mcp.cli'`.

- [ ] **Step 3: Implement `cli.py`**

```python
"""Console entry point for ``guap-teacher``.

Subcommands: ``init`` (seed personal skill copies), ``skills diff``
(compare them with the canonical ones). Without a subcommand the MCP
server starts on stdio exactly as before, so existing MCP client configs
keep working.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from guap_teacher_mcp import distribute, skills

# Publication URL: the repository lives at github.com/MADTeacher/guap-teacher-mcp.
PACKAGE_SOURCE = "git+https://github.com/MADTeacher/guap-teacher-mcp"

MCP_SNIPPETS = f"""\
Подключение MCP-сервера (stdio) в вашем харнессе:

ZCode (settings, mcpServers):
  {{"mcpServers": {{"guap-teacher": {{"command": "uvx", "args": ["--from", "{PACKAGE_SOURCE}", "guap-teacher"]}}}}}}

Codex (~/.codex/config.toml):
  [mcp_servers.guap-teacher]
  command = "uvx"
  args = ["--from", "{PACKAGE_SOURCE}", "guap-teacher"]

Qwen Code (~/.qwen/settings.json):
  {{"mcpServers": {{"guap-teacher": {{"command": "uvx", "args": ["--from", "{PACKAGE_SOURCE}", "guap-teacher"]}}}}}}

Локальный clone вместо uvx:
  uv --directory <путь к guap-teacher-mcp> run guap-teacher
"""

_DIFF_HINTS = {
    "missing": " — нет в личном каталоге; guap-teacher init доустановит",
    "differs": " — личная копия отличается от канона (это нормально)",
    "identical": " — совпадает с каноном",
}


def _personal_root(value: str | None) -> Path:
    return Path(value) if value else skills.personal_skills_root()


def _cmd_init(args: argparse.Namespace) -> int:
    canonical_root = skills.canonical_skills_root()
    personal_root = _personal_root(args.skills_dir)
    result = distribute.seed_personal_skills(canonical_root, personal_root)
    print(f"Личный каталог навыков: {personal_root}")
    if result.seeded:
        print("Установлены: " + ", ".join(result.seeded))
    if result.skipped:
        print("Пропущены (уже существуют, не перезаписаны): " + ", ".join(result.skipped))
    if not result.seeded and not result.skipped:
        print("Канонические навыки не найдены.")
    print()
    print(MCP_SNIPPETS)
    return 0


def _cmd_skills_diff(args: argparse.Namespace) -> int:
    canonical_root = skills.canonical_skills_root()
    personal_root = _personal_root(args.skills_dir)
    for item in distribute.diff_personal_skills(canonical_root, personal_root):
        print(f"{item.name}: {item.status}{_DIFF_HINTS[item.status]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args; without a subcommand start the MCP server (stdio)."""
    parser = argparse.ArgumentParser(
        prog="guap-teacher",
        description="MCP-сервер guap-teacher и утилиты распространения навыков",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser(
        "init", help="посеять канонические навыки в личный каталог (~/.agents/skills)"
    )
    p_init.add_argument(
        "--skills-dir",
        default=None,
        help="каталог личных навыков (по умолчанию GUAP_SKILLS_DIR или ~/.agents/skills)",
    )
    p_init.set_defaults(func=_cmd_init)

    p_skills = sub.add_parser("skills", help="операции с навыками")
    skills_sub = p_skills.add_subparsers(dest="skills_command")
    p_diff = skills_sub.add_parser(
        "diff", help="сравнить личные копии навыков с каноном текущей версии"
    )
    p_diff.add_argument(
        "--skills-dir",
        default=None,
        help="каталог личных навыков (по умолчанию GUAP_SKILLS_DIR или ~/.agents/skills)",
    )
    p_diff.set_defaults(func=_cmd_skills_diff)

    args = parser.parse_args(argv)

    if args.command == "skills" and not getattr(args, "skills_command", None):
        parser.error("skills: укажите подкоманду (diff)")

    func = getattr(args, "func", None)
    if func is None:
        # No subcommand: behave exactly like the old console script.
        from guap_teacher_mcp.server import main as serve  # lazy: heavy imports

        serve()
        return 0
    return func(args)
```

- [ ] **Step 4: Switch the console script in `pyproject.toml`**

```toml
[project.scripts]
guap-teacher = "guap_teacher_mcp.cli:main"
```

- [ ] **Step 5: Run tests and smoke-check the CLI**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (3 теста).

Run: `uv run guap-teacher --help`
Expected: справка с подкомандами init / skills печатается, exit code 0.

Run: `uv run guap-teacher skills`
Expected: ошибка argparse с подсказкой «skills: укажите подкоманду (diff)», exit code 2.

- [ ] **Step 6: Commit**

```bash
git add src/guap_teacher_mcp/cli.py tests/test_cli.py pyproject.toml
git commit -m "feat: guap-teacher init / skills diff subcommands (serve stays default)"
```

---

### Task 5: Package data — канонические навыки едут в wheel

**Files:**
- Modify: `pyproject.toml` (`[tool.hatch.build.targets.wheel.force-include]`)
- Test: `tests/test_skills.py` (добавить тест корня при установленном пакете — опционально, см. Step 3)

**Interfaces:**
- Consumes: `skills.canonical_skills_root()` из Task 1 (prefers `Path(__file__).parent / "skills"`).
- Produces: wheel содержит `guap_teacher_mcp/skills/<имя>/SKILL.md`; `uvx --from git+… guap-teacher init` работает без clone репозитория.

- [ ] **Step 1: Add force-include to `pyproject.toml`**

Сразу после блока `[tool.hatch.build.targets.wheel]`:

```toml
[tool.hatch.build.targets.wheel.force-include]
"skills" = "guap_teacher_mcp/skills"
```

- [ ] **Step 2: Build and inspect the wheel**

Run: `uv build && python -m zipfile -l dist/guap_teacher_mcp-*.whl | grep "guap_teacher_mcp/skills/"`
Expected: в списке файлов `guap_teacher_mcp/skills/guap-review/SKILL.md`, `…/guap-schedule/SKILL.md` и т.д. (все пять навыков).

- [ ] **Step 3: Verify canonical root resolution from a built install (offline)**

Установить wheel во временный venv и проверить, что корень указывает внутрь пакета:

```bash
uv venv .tmp_pkgtest && uv pip install --python .tmp_pkgtest dist/guap_teacher_mcp-*.whl && \
.tmp_pkgtest/Scripts/python -c "from guap_teacher_mcp.skills import canonical_skills_root; r = canonical_skills_root(); assert 'site-packages' in str(r) and (r / 'guap-review' / 'SKILL.md').is_file(), r; print('OK:', r)"
rm -rf .tmp_pkgtest dist
```

Expected: `OK: …site-packages…guap_teacher_mcp\skills`. (Каталог `.tmp_pkgtest` и `dist` не коммитить; проверить, что они в `.gitignore`, при отсутствии — добавить `dist/` и `.tmp_pkgtest/` в этот шаг.)

- [ ] **Step 4: Run the full test suite**

Run: `uv run pytest`
Expected: PASS (все файлы).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "build: ship canonical skills as wheel package data (force-include)"
```

---

### Task 6: Раздел «Настройка под себя» в канонических навыках

**Files:**
- Modify: `skills/guap-schedule/SKILL.md`, `skills/guap-review/SKILL.md`, `skills/guap-kurs-review/SKILL.md`, `skills/guap-vedomost/SKILL.md`, `skills/guap-digest/SKILL.md` (в конец каждого — один и тот же раздел, `<имя>` подставить)
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: —
- Produces: каждый канонический навык сам объясняет агенту, где личная копия и как её править (требование спеки).

- [ ] **Step 1: Write the failing test**

Добавить в `tests/test_skills.py`:

```python
def test_canonical_skills_document_customization_section():
    """Every canonical skill must explain where the personal copy lives."""
    for skill in load_skills(REPO_SKILLS):
        assert "## Настройка под себя" in skill.markdown, skill.name
        assert "~/.agents/skills" in skill.markdown, skill.name
        assert "guap-teacher skills diff" in skill.markdown, skill.name
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills.py::test_canonical_skills_document_customization_section -v`
Expected: FAIL — asserts не проходят ни для одного навыка.

- [ ] **Step 3: Append the section to each of the five SKILL.md files**

В конец каждого `skills/<имя>/SKILL.md` (без изменений остального текста; `<имя>` — имя каталога навыка):

```markdown

## Настройка под себя

Это канонический текст — отправная точка, а не догма. Личная копия
преподавателя: `~/.agents/skills/<имя>/SKILL.md` (создаётся
`guap-teacher init`; каталог переопределяется переменной GUAP_SKILLS_DIR).
Правь её под свои правила приёмки и оценивания — сам или попроси агента
(«титульник не проверяй, зато ругай за отсутствие тестов»); ZCode, Codex
и Qwen Code читают её напрямую. Обновления движка личную копию не
трогают; сравнить с каноном: `guap-teacher skills diff`.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/
git commit -m "docs(skills): add 'Настройка под себя' section pointing to ~/.agents/skills"
```

---

### Task 7: README и AGENTS.md — распространение и настройка

**Files:**
- Modify: `README.md` (секция «Установка» → новая «Установка (преподавателю)» + «Настройка под себя»; секция «Агентские навыки» — абзац про `GUAP_SKILLS_DIR` и «Ограничение ZCode»)
- Modify: `AGENTS.md` (блок «Структура» — две новые строки)

**Interfaces:**
- Consumes: поведение из Task 1–6 (`init`, `skills diff`, `GUAP_SKILLS_DIR`, package data).
- Produces: агент-читаемая инструкция установки (не-технарь ставит «разговором»), актуальные документы репозитория.

- [ ] **Step 1: README — заменить секцию «Установка» (строки после заголовка `## Установка` до `## Запуск`) на:**

````markdown
## Установка (преподавателю)

Понадобятся [uv](https://docs.astral.sh/uv/) и агент-харнесс, читающий
`~/.agents/skills` (ZCode, Codex, Qwen Code; Claude Code не поддерживается).

```bash
uvx --from git+https://github.com/MADTeacher/guap-teacher-mcp guap-teacher init
```

`init` сеет канонические навыки в `~/.agents/skills/guap-*` (существующие
файлы не перезаписывает) и печатает сниппеты MCP-конфига для ZCode /
Codex / Qwen Code — вставьте подходящий в конфиг вашего харнесса.
`guap-teacher` без аргументов — запуск MCP-сервера (stdio).

Проще всего попросить своего агента: «поставь guap-teacher отсюда
<ссылка на репозиторий>, подключи MCP и настрой навыки под мои правила
приёмки работ» — агент прочитает этот README и выполнит шаги сам.

Обновление движка (например, когда изменилась вёрстка портала):

```bash
uvx --refresh --from git+https://github.com/MADTeacher/guap-teacher-mcp guap-teacher --help
```

или просто попросите агента «обнови guap-teacher». Личные копии навыков
при этом не затрагиваются.
````

- [ ] **Step 2: README — в секции «Агентские навыки (Skills over MCP)» заменить абзац про `GUAP_SKILLS_DIR` и абзац «**Ограничение ZCode:** …» на:**

```markdown
Личные копии навыков преподавателя живут в `~/.agents/skills/<имя>/`
(каталог по умолчанию; переопределяется `GUAP_SKILLS_DIR`). ZCode, Codex
и Qwen Code читают этот каталог нативно; MCP-ресурсы `skill://` отдают
те же навыки любому клиенту с `resources/list` / `resources/read`
(личная копия побеждает при совпадении имени). Канонические навыки едут
внутри пакета; сравнить личные копии с каноном —
`guap-teacher skills diff`. Стабы `.zcode/skills/` остаются только для
разработки в самом репозитории.
```

(Существующий в конце секции абзац «Новый навык: создать `skills/<имя>/SKILL.md`…» сохранить как есть.)

- [ ] **Step 3: AGENTS.md — в блок «Структура» добавить после строки `skills.py`:**

```
  distribute.py # посев/сравнение личных копий навыков (~/.agents/skills)
  cli.py        # подкоманды guap-teacher: init, skills diff (без аргументов — сервер)
```

и дополнить строку `skills.py` (загрузка навыков и ресурсы skill://) словами про двухкорневое разрешение (личный `~/.agents/skills` побеждает канон).

- [ ] **Step 4: Финальная проверка всего плана**

Run: `uv run pytest`
Expected: PASS (все тесты).

Run: `uv run python -c "import guap_teacher_mcp.server"`
Expected: без ошибок.

Run: `uv run guap-teacher skills diff`
Expected: статусы по всем пяти каноническим навыкам (скорее всего `missing` — личный каталог ещё не сеялся на этой машине; после `uv run guap-teacher init` повторный diff покажет `identical`/`differs`). **Внимание: `uv run guap-teacher init` на этой машине не выполнять** — она разработческая, личные навыки владельца в `~/.agents/skills` не сеем без явного решения.

- [ ] **Step 5: Commit**

```bash
git add README.md AGENTS.md
git commit -m "docs: distribution & customization — uvx install, ~/.agents/skills, skills diff"
```
