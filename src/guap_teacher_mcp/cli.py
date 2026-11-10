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

# Publication URL: replace <owner> once the repository gets its GitHub
# remote (open item tracked in the design spec).
PACKAGE_SOURCE = "git+https://github.com/<owner>/guap-teacher-mcp"

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

    skills_dir = getattr(args, "skills_dir", None)
    if skills_dir is not None and not skills_dir.strip():
        parser.error("--skills-dir: путь не может быть пустым")

    if args.command == "skills" and not getattr(args, "skills_command", None):
        parser.error("skills: укажите подкоманду (diff)")

    func = getattr(args, "func", None)
    if func is None:
        # No subcommand: behave exactly like the old console script.
        from guap_teacher_mcp.server import main as serve  # lazy: heavy imports

        serve()
        return 0
    return func(args)
